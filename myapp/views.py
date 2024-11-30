from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from .models import Room, RoleAssignment, Player, BugReport, UserProfile
from .forms import RoomCreationForm, JoinRoomForm, PlayerForm, CustomUserCreationForm, BugReportForm
import random
import string
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from django.utils import timezone
from datetime import timedelta
from django.db.models import F
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.urls import reverse
from .utils import get_device_type
from django.views.decorators.http import require_POST
from django.db import DatabaseError
from django.template.loader import render_to_string
from .utils.changelog import get_changelog
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError
from .utils.turnstile import verify_turnstile
from .utils.email import generate_verification_code, send_verification_email, send_password_reset_email
from django.core.cache import cache
from django.utils.translation import gettext as _
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator

ROLE_INFO = {
    'MAFIA': {
        'description': 'A member of the mafia team trying to eliminate the villagers.',
        'objective': 'Eliminate all villagers while keeping your identity hidden.',
        'tips': [
            'Stay calm during discussions',
            'Create believable alibis',
            'Coordinate with other mafia members',
            'Try to cast suspicion on others',
            'Be careful not to defend other mafia members too obviously'
        ],
        'icon': 'fa-skull',
        'color': 'danger'
    },
    'DOCTOR': {
        'description': 'A villager with the power to save one person each night.',
        'objective': 'Keep villagers alive and help identify the mafia.',
        'tips': [
            'Pay attention to voting patterns',
            'Keep your identity hidden from the mafia',
            'Consider saving yourself occasionally',
            'Watch for patterns in mafia attacks',
            'Coordinate with the cop when revealed'
        ],
        'icon': 'fa-user-md',
        'color': 'success'
    },
    'COP': {
        'description': 'A villager who can investigate one player each night.',
        'objective': 'Identify mafia members and lead the village to victory.',
        'tips': [
            'Keep notes of your investigations',
            'Be strategic about revealing your findings',
            'Watch for suspicious behavior',
            'Consider the timing of revealing your role',
            'Build trust with confirmed villagers'
        ],
        'icon': 'fa-user-shield',
        'color': 'info'
    },
    'VILLAGER': {
        'description': 'A regular townsperson trying to identify the mafia.',
        'objective': 'Work with other villagers to identify and eliminate all mafia members.',
        'tips': [
            'Pay attention to everyone\'s behavior',
            'Take notes during discussions',
            'Share your observations',
            'Vote based on evidence, not emotions',
            'Support the special roles when they reveal themselves'
        ],
        'icon': 'fa-user',
        'color': 'light'
    }
}

def home(request):
    return render(request, 'myapp/home.html')

@login_required
def create_room(request):
    if request.method == 'POST':
        form = RoomCreationForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.host = request.user
            room.room_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            room.save()
            
            # Ensure the host has a session key
            if not request.session.session_key:
                request.session.create()
                
            # Create a Player object for the host
            host_player = Player.objects.create(
                name=request.user.username,
                session_key=request.session.session_key,
                device_order=0
            )
            room.temp_players.add(host_player)
            
            return redirect('waiting_room', room_code=room.room_code)
    else:
        form = RoomCreationForm()
    return render(request, 'myapp/create_room.html', {'form': form})

def join_room(request):
    if request.method == 'POST':
        room_form = JoinRoomForm(request.POST)
        player_count = int(request.POST.get('player_count', 1))
        token = request.POST.get('cf-turnstile-response')
        
        try:
            verify_turnstile(token)
            if room_form.is_valid():
                room_code = room_form.cleaned_data['room_code']
                password = room_form.cleaned_data['password']
                
                try:
                    room = Room.objects.get(room_code=room_code)
                    
                    # Check if user is banned
                    if request.user.is_authenticated and room.banned_users.filter(id=request.user.id).exists():
                        messages.error(request, 'You are banned from this room')
                        return redirect('home')
                    
                    # Check password if room is password protected
                    if room.is_password_protected() and room.password != password:
                        messages.error(request, 'Invalid password')
                        return render(request, 'myapp/join_room.html', {
                            'room_form': room_form
                        })
                    
                    # Create players for this device
                    if not request.session.session_key:
                        request.session.create()
                    
                    for i in range(player_count):
                        player_name = request.POST.get(f'player_name_{i}')
                        if player_name:
                            player = Player.objects.create(
                                name=player_name,
                                session_key=request.session.session_key,
                                device_order=i
                            )
                            room.temp_players.add(player)
                
                    return redirect('waiting_room', room_code=room_code)
                except Room.DoesNotExist:
                    messages.error(request, 'Invalid room code')
        except ValidationError as e:
            room_form.add_error(None, str(e))
    else:
        room_form = JoinRoomForm()
    
    return render(request, 'myapp/join_room.html', {
        'room_form': room_form
    })

def _get_player_list_html(room):
    players = list(room.players.all()) + list(room.temp_players.all())
    html = ''
    for player in players:
        if hasattr(player, 'username'):
            name = player.username
        else:
            name = player.name
        host_badge = '<span class="badge bg-primary">Host</span>' if player == room.host else ''
        html += f'<li class="list-group-item">{name} {host_badge}</li>'
    return html

def waiting_room(request, room_code):
    room = get_object_or_404(Room, room_code=room_code)
    is_host = request.user.is_authenticated and request.user == room.host
    device_type = get_device_type(request)
    
    # Get all players (both authenticated and temporary)
    players = list(room.players.all()) + list(room.temp_players.all())
    
    context = {
        'room': room,
        'is_host': is_host,
        'players': players,
        'device_type': device_type,
    }
    return render(request, 'myapp/waiting_room.html', context)

@login_required
def assign_roles(request, room_code):
    room = get_object_or_404(Room, room_code=room_code)
    if request.user != room.host:
        messages.error(request, 'Only the host can assign roles')
        return redirect('waiting_room', room_code=room_code)

    # Get all players (both authenticated and temporary)
    all_players = list(room.players.all()) + list(room.temp_players.all())
    roles = (['MAFIA'] * room.mafia_count +
             ['DOCTOR'] * room.doctor_count +
             ['COP'] * room.cop_count)
    
    # Fill remaining with villagers
    roles += ['VILLAGER'] * (len(all_players) - len(roles))
    random.shuffle(roles)

    # Clear existing assignments
    RoleAssignment.objects.filter(room=room).delete()
    
    # Assign roles to all players
    for player, role in zip(all_players, roles):
        RoleAssignment.objects.create(
            user=player if isinstance(player, User) else None,
            temp_player=player if isinstance(player, Player) else None,
            room=room,
            role=role
        )
    
    room.special_role_assigned = True
    room.save()
    
    return redirect('role_display', room_code=room_code)

def role_display(request, room_code):
    room = get_object_or_404(Room, room_code=room_code)
    show_role = request.GET.get('show_role', False)
    
    # Get all players for this device
    session_key = request.session.session_key
    device_players = Player.objects.filter(
        session_key=session_key,
        joined_rooms=room
    ).order_by('device_order')
    
    # Find first player who hasn't viewed their role
    current_player = device_players.filter(has_viewed_role=False).first()
    
    if current_player:
        role_assignment = get_object_or_404(
            RoleAssignment,
            temp_player=current_player,
            room=room
        )
        # Add role information to context
        role_info = ROLE_INFO.get(role_assignment.role, {})
    else:
        role_assignment = None
        role_info = None
        show_role = False
    
    return render(request, 'myapp/role_display.html', {
        'room': room,
        'current_player': current_player,
        'role_assignment': role_assignment,
        'show_role': show_role,
        'role_info': role_info
    })

def leave_room(request, room_code):
    room = get_object_or_404(Room, room_code=room_code)
    
    if request.user.is_authenticated:
        if request.user == room.host:
            room.delete()
        else:
            room.players.remove(request.user)
    else:
        # Remove temporary player
        temp_player = room.temp_players.filter(session_key=request.session.session_key).first()
        if temp_player:
            room.temp_players.remove(temp_player)
            temp_player.delete()
    
    return redirect('home')

def get_player_list(request, room_code):
    room = get_object_or_404(Room, room_code=room_code)
    players = list(room.players.all()) + list(room.temp_players.all())
    is_host = request.user.is_authenticated and request.user == room.host
    
    # Add player count badge HTML
    player_count_html = f'''
        <h3>
            <i class="fas fa-users me-2"></i>Players
            <span class="badge bg-primary">{len(players)}</span>
        </h3>
    '''
    
    player_list_html = ''
    for player in players:
        # Determine if player is host
        is_player_host = (isinstance(player, User) and player == room.host) or \
                        (isinstance(player, Player) and player.name == room.host.username)
        
        # Get player name
        if isinstance(player, User):
            name = player.username
            player_id = player.id
        else:
            name = player.name
            player_id = player.id
            
        # Set action buttons based on player type and host status
        if is_player_host:
            # Host badge only, no action buttons
            action_buttons = '<span class="badge bg-primary"><i class="fas fa-crown me-1"></i>Host</span>'
        elif is_host:
            # Show appropriate action buttons for non-host players
            if isinstance(player, User):
                # Registered users get kick and ban buttons
                action_buttons = f'''
                    <div class="btn-group">
                        <a href="{reverse("kick_player", kwargs={"room_code": room.room_code, "player_id": player_id})}"
                           class="btn btn-sm btn-warning"
                           onclick="return confirm('Are you sure you want to kick {name}?')">
                            <i class="fas fa-user-times me-1"></i>Kick
                        </a>
                        <a href="{reverse('ban_player', kwargs={'room_code': room.room_code, 'player_id': player_id})}"
                           class="btn btn-sm btn-danger"
                           onclick="return confirm('Are you sure you want to ban {name}? They will not be able to rejoin this room.')">
                            <i class="fas fa-ban me-1"></i>Ban
                        </a>
                    </div>
                '''
            else:
                # Temporary players only get kick button
                action_buttons = f'''
                    <a href="{reverse("kick_player", kwargs={"room_code": room.room_code, "player_id": player_id})}"
                       class="btn btn-sm btn-warning"
                       onclick="return confirm('Are you sure you want to kick {name}?')">
                        <i class="fas fa-user-times me-1"></i>Kick
                    </a>
                '''
        else:
            action_buttons = ''

        player_list_html += f'''
            <li class="list-group-item d-flex justify-content-between align-items-center">
                <span><i class="fas fa-user me-2"></i>{name}</span>
                {action_buttons}
            </li>
        '''
    
    # Check if roles have been assigned
    roles_assigned = room.special_role_assigned
    
    return JsonResponse({
        'player_list_html': player_list_html,
        'player_count_html': player_count_html,
        'roles_assigned': roles_assigned,
        'total_players': len(players)
    })

def mark_ready(request, room_code):
    room = get_object_or_404(Room, room_code=room_code)
    
    # Increment the ready count
    room.players_ready = F('players_ready') + 1
    room.save()
    
    # Refresh from database to get actual count
    room.refresh_from_db()
    
    # If all players are ready, set the timestamp
    total_players = room.players.count() + room.temp_players.count()
    if room.players_ready >= total_players and not room.all_ready_at:
        room.all_ready_at = timezone.now()
        room.save()
    
    return redirect('home')

def check_room_status(request, room_code):
    room = get_object_or_404(Room, room_code=room_code)
    room_deleted = False
    
    if room.all_ready_at:
        # Check if 10 minutes have passed since all players were ready
        if timezone.now() >= room.all_ready_at + timedelta(minutes=10):
            room.delete()
            room_deleted = True
    
    return JsonResponse({
        'room_deleted': room_deleted
    })

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        token = request.POST.get('cf-turnstile-response')
        try:
            verify_turnstile(token)
            if form.is_valid():
                # Create user but don't save yet
                user = form.save(commit=False)
                user.is_active = False  # User won't be able to login until email is verified
                user.save()
                
                # Create user profile
                verification_code = generate_verification_code()
                profile = UserProfile.objects.create(
                    user=user,
                    verification_code=verification_code,
                    verification_code_created=timezone.now()
                )
                
                # Send verification email
                if send_verification_email(user, verification_code):
                    return redirect('verify_email', user_id=user.id)
                else:
                    messages.error(request, 'Failed to send verification email. Please try again.')
                    user.delete()
                    return redirect('register')
                    
        except ValidationError as e:
            form.add_error(None, str(e))
    else:
        form = CustomUserCreationForm()
    return render(request, 'myapp/register.html', {'form': form})

def verify_email(request, user_id):
    try:
        profile = UserProfile.objects.get(user_id=user_id)
        if request.method == 'POST':
            code = request.POST.get('verification_code')
            
            # Check if code is expired (24 hours)
            if timezone.now() > profile.verification_code_created + timedelta(hours=24):
                messages.error(request, 'Verification code has expired. Please request a new one.')
                return redirect('resend_verification')
                
            if code == profile.verification_code:
                profile.user.is_active = True
                profile.email_verified = True
                profile.user.save()
                profile.save()
                messages.success(request, 'Email verified successfully! You can now login.')
                return redirect('login')
            else:
                messages.error(request, 'Invalid verification code. Please try again.')
                
        return render(request, 'myapp/verify_email.html', {'user_id': user_id})
    except UserProfile.DoesNotExist:
        messages.error(request, 'Invalid user.')
        return redirect('register')

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep user logged in
            messages.success(request, 'Your password was successfully updated!')
            return redirect('home')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'myapp/change_password.html', {'form': form})

@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        # Check if user is not an admin
        if not user.is_superuser and not user.is_staff:
            user.delete()
            messages.success(request, 'Your account has been successfully deleted.')
            return redirect('home')
        else:
            messages.error(request, 'Admin accounts cannot be deleted.')
    return render(request, 'myapp/delete_account.html')

def report_bug(request):
    if request.method == 'POST':
        form = BugReportForm(request.POST)
        if form.is_valid():
            bug_report = form.save(commit=False)
            if request.user.is_authenticated:
                bug_report.reporter = request.user
            bug_report.save()
            messages.success(request, 'Bug report submitted successfully!')
            return redirect('bug_list')
    else:
        form = BugReportForm()
    return render(request, 'myapp/report_bug.html', {'form': form})

def bug_list(request):
    if request.user.is_staff:
        # Staff can see all bugs
        bugs = BugReport.objects.all().order_by('-created_at')
        can_edit = True
    elif request.user.is_authenticated:
        # Users can see their own reported bugs
        bugs = BugReport.objects.filter(reporter=request.user).order_by('-created_at')
        can_edit = True
    else:
        # Guest users can see all bugs but can't edit
        bugs = BugReport.objects.all().order_by('-created_at')
        can_edit = False
    
    return render(request, 'myapp/bug_list.html', {
        'bugs': bugs,
        'can_edit': can_edit
    })

@login_required
def bug_detail(request, bug_id):
    bug = get_object_or_404(BugReport, id=bug_id)
    if not request.user.is_staff and bug.reporter != request.user:
        messages.error(request, 'You do not have permission to view this bug report.')
        return redirect('bug_list')
    return render(request, 'myapp/bug_detail.html', {'bug': bug})

@login_required
def kick_player(request, room_code, player_id):
    room = get_object_or_404(Room, room_code=room_code)
    
    # Verify that the request is from the host
    if request.user != room.host:
        messages.error(request, 'Only the host can kick players')
        return redirect('waiting_room', room_code=room_code)
    
    # Get the player to kick (could be User or TempPlayer)
    kicked_user = get_object_or_404(User, id=player_id)
    
    # Prevent host from kicking themselves
    if kicked_user == room.host:
        messages.error(request, 'Host cannot kick themselves')
        return redirect('waiting_room', room_code=room_code)
    
    # Remove the player from the room
    if kicked_user in room.players.all():
        room.players.remove(kicked_user)
    elif kicked_user in room.temp_players.all():
        room.temp_players.remove(kicked_user)
        
    messages.success(request, f'Successfully kicked {kicked_user.username or kicked_user.name}')
    return redirect('waiting_room', room_code=room_code)

@login_required 
def ban_player(request, room_code, player_id):
    room = get_object_or_404(Room, room_code=room_code)
    
    # Verify that the request is from the host
    if request.user != room.host:
        messages.error(request, 'Only the host can ban players')
        return redirect('waiting_room', room_code=room_code)
    
    # Get the player to ban
    banned_user = get_object_or_404(User, id=player_id)
    
    # Prevent host from banning themselves
    if banned_user == room.host:
        messages.error(request, 'Host cannot ban themselves')
        return redirect('waiting_room', room_code=room_code)
    
    # Remove and ban the player
    if banned_user in room.players.all():
        room.players.remove(banned_user)
    elif banned_user in room.temp_players.all():
        room.temp_players.remove(banned_user)
        
    room.banned_players.add(banned_user)
    messages.success(request, f'Successfully banned {banned_user.username or banned_user.name}')
    return redirect('waiting_room', room_code=room_code)

def mark_role_viewed(request, room_code):
    if request.method == 'POST':
        room = get_object_or_404(Room, room_code=room_code)
        session_key = request.session.session_key
        
        # Get current player
        current_player = Player.objects.filter(
            session_key=session_key,
            joined_rooms=room,
            has_viewed_role=False
        ).order_by('device_order').first()
        
        if current_player:
            current_player.has_viewed_role = True
            current_player.save()
        
        return JsonResponse({'redirect': True})
    
    return JsonResponse({'redirect': False})

@require_POST
def update_roles(request, room_code):
    try:
        room = get_object_or_404(Room, room_code=room_code)
        if request.user != room.host:
            return JsonResponse({'success': False, 'error': 'Only the host can update roles'})
        
        data = json.loads(request.body)
        
        # Update room settings
        room.mafia_count = int(data.get('mafia_count', 1))
        room.doctor_count = int(data.get('doctor_count', 0))
        room.cop_count = int(data.get('cop_count', 0))
        
        # Validate role counts
        total_players = room.players.count() + room.temp_players.count()
        total_special_roles = room.mafia_count + room.doctor_count + room.cop_count
        
        if total_special_roles >= total_players:
            return JsonResponse({
                'success': False, 
                'error': 'Total special roles must be less than number of players'
            })
        
        if total_players < 4:
            return JsonResponse({
                'success': False, 
                'error': 'Need at least 4 players to start the game'
            })
        
        if room.mafia_count < 1:
            return JsonResponse({
                'success': False, 
                'error': 'Must have at least 1 mafia'
            })
        
        room.save()
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def handle_db_operation(view_func):
    """Decorator to handle database operations."""
    def wrapper(*args, **kwargs):
        try:
            return view_func(*args, **kwargs)
        except DatabaseError as e:
            messages.error(args[0], f"Database error: {str(e)}")
            return redirect('home')
    return wrapper

@handle_db_operation
def your_view(request):
    # Your view code here
    pass

def changelog(request):
    """Display the changelog page"""
    changelog_data = get_changelog()
    return render(request, 'myapp/changelog.html', {
        'changelog': changelog_data
    })

class CustomLoginView(LoginView):
    template_name = 'myapp/login.html'
    
    def form_valid(self, form):
        token = self.request.POST.get('cf-turnstile-response')
        try:
            verify_turnstile(token)
        except ValidationError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)
        return super().form_valid(form)

def resend_verification(request, user_id):
    try:
        # Check rate limiting
        cache_key = f'resend_email_{user_id}'
        if cache.get(cache_key):
            messages.error(request, _('Please wait at least 1 minute before requesting another code.'))
            return redirect('verify_email', user_id=user_id)
            
        profile = UserProfile.objects.get(user_id=user_id)
        
        # Generate new verification code
        verification_code = generate_verification_code()
        profile.verification_code = verification_code
        profile.verification_code_created = timezone.now()
        profile.save()
        
        # Send new verification email
        if send_verification_email(profile.user, verification_code):
            messages.success(request, _('A new verification code has been sent to your email.'))
            # Set rate limit for 1 minute
            cache.set(cache_key, True, 60)
        else:
            messages.error(request, _('Failed to send verification email. Please try again.'))
            
        return redirect('verify_email', user_id=user_id)
        
    except UserProfile.DoesNotExist:
        messages.error(request, _('Invalid user.'))
        return redirect('register')

def password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            if send_password_reset_email(user):
                messages.success(request, 'Password reset link has been sent to your email.')
            else:
                messages.error(request, 'Failed to send reset email. Please try again.')
        except User.DoesNotExist:
            # Still show success message for security
            messages.success(request, 'Password reset link has been sent to your email.')
        return redirect('login')
    return render(request, 'myapp/password_reset.html')

def password_reset_confirm(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password1 = request.POST.get('new_password1')
            password2 = request.POST.get('new_password2')
            
            if password1 and password2 and password1 == password2:
                user.set_password(password1)
                user.save()
                messages.success(request, 'Your password has been reset successfully!')
                return redirect('login')
            else:
                messages.error(request, 'Passwords do not match.')
        return render(request, 'myapp/password_reset_confirm.html', {'validlink': True})
    else:
        return render(request, 'myapp/password_reset_confirm.html', {'validlink': False})
