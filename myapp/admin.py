from django.contrib import admin
from .models import Room, RoleAssignment, BugReport

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_name', 'room_code', 'host', 'created_at', 'special_role_assigned')
    search_fields = ('room_name', 'room_code', 'host__username')
    list_filter = ('special_role_assigned', 'created_at')

@admin.register(RoleAssignment)
class RoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'room', 'role', 'assigned_at')
    list_filter = ('role',)
    search_fields = ('user__username', 'room__room_name')

@admin.register(BugReport)
class BugReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'priority', 'reporter', 'created_at', 'updated_at')
    list_filter = ('status', 'priority', 'created_at')
    search_fields = ('title', 'description', 'reporter__username')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Bug Information', {
            'fields': ('title', 'description', 'steps_to_reproduce', 'priority', 'status')
        }),
        ('Reporter Information', {
            'fields': ('reporter', 'created_at', 'updated_at')
        }),
        ('Admin Notes', {
            'fields': ('admin_notes',),
            'classes': ('collapse',)
        })
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ('reporter',)
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new bug report
            if not obj.reporter:
                obj.reporter = request.user
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete bug reports
        return request.user.is_superuser
