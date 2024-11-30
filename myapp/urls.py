from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import CustomLoginView

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('create-room/', views.create_room, name='create_room'),
    path('join-room/', views.join_room, name='join_room'),
    path('room/<str:room_code>/', views.waiting_room, name='waiting_room'),
    path('room/<str:room_code>/assign-roles/', views.assign_roles, name='assign_roles'),
    path('room/<str:room_code>/leave/', views.leave_room, name='leave_room'),
    path('role/<str:room_code>/', views.role_display, name='role_display'),
    path('room/<str:room_code>/players/', views.get_player_list, name='get_player_list'),
    path('room/<str:room_code>/mark-ready/', views.mark_ready, name='mark_ready'),
    path('room/<str:room_code>/status/', views.check_room_status, name='check_room_status'),
    path('register/', views.register, name='register'),
    path('change-password/', views.change_password, name='change_password'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('report-bug/', views.report_bug, name='report_bug'),
    path('bugs/', views.bug_list, name='bug_list'),
    path('bug/<int:bug_id>/', views.bug_detail, name='bug_detail'),
    path('room/<str:room_code>/kick/<int:player_id>/', views.kick_player, name='kick_player'),
    path('room/<str:room_code>/ban/<int:player_id>/', views.ban_player, name='ban_player'),
    path('role/<str:room_code>/mark-viewed/', views.mark_role_viewed, name='mark_role_viewed'),
    path('room/<str:room_code>/update-roles/', views.update_roles, name='update_roles'),
    path('changelog/', views.changelog, name='changelog'),
    path('verify-email/<int:user_id>/', views.verify_email, name='verify_email'),
    path('resend-verification/<int:user_id>/', views.resend_verification, name='resend_verification'),
    path('reset-password/', views.password_reset, name='password_reset'),
    path('reset-password/<str:uidb64>/<str:token>/', views.password_reset_confirm, name='password_reset_confirm'),
] 