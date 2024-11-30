from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class Player(models.Model):
    name = models.CharField(max_length=100)
    session_key = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    device_order = models.IntegerField(default=0)
    has_viewed_role = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Room(models.Model):
    room_name = models.CharField(max_length=100)
    room_code = models.CharField(max_length=6, unique=True)
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_rooms')
    players = models.ManyToManyField(User, related_name='joined_rooms')
    temp_players = models.ManyToManyField(Player, related_name='joined_rooms')
    mafia_count = models.IntegerField(default=1)
    doctor_count = models.IntegerField(default=1)
    cop_count = models.IntegerField(default=1)
    special_role_assigned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    players_ready = models.IntegerField(default=0)
    all_ready_at = models.DateTimeField(null=True, blank=True)
    password = models.CharField(max_length=128, blank=True, null=True)
    banned_users = models.ManyToManyField(User, related_name='banned_from_rooms', blank=True)

    def clean(self):
        if self.id:
            total_special_roles = self.mafia_count + self.doctor_count + self.cop_count
            player_count = self.players.count() + self.temp_players.count()
            if total_special_roles >= player_count:
                raise ValidationError("Number of special roles cannot exceed number of players")

    def is_password_protected(self):
        return bool(self.password)

    def check_password(self, password):
        return self.password == password

    def __str__(self):
        return f"{self.room_name} ({self.room_code})"

class RoleAssignment(models.Model):
    ROLE_CHOICES = [
        ('MAFIA', 'Mafia'),
        ('DOCTOR', 'Doctor'),
        ('COP', 'Cop'),
        ('VILLAGER', 'Villager'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    temp_player = models.ForeignKey(Player, on_delete=models.CASCADE, null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [
            ('user', 'room'),
            ('temp_player', 'room'),
        ]

    def clean(self):
        if not self.user and not self.temp_player:
            raise ValidationError("Either user or temp_player must be set")
        if self.user and self.temp_player:
            raise ValidationError("Cannot set both user and temp_player")

    def __str__(self):
        player = self.user.username if self.user else self.temp_player.name
        return f"{player} - {self.role} in {self.room.room_name}"

class BugReport(models.Model):
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical')
    ]
    
    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed')
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    steps_to_reproduce = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    reporter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reported_bugs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} - {self.priority} Priority"