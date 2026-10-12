from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Ticket, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile & Role'


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'profile__role')

    def get_role(self, obj):
        return obj.profile.get_role_display() if hasattr(obj, 'profile') else 'Customer'
    get_role.short_description = 'Support Role'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        'ticket_id',
        'title',
        'customer',
        'category',
        'priority',
        'status',
        'assigned_to',
        'created_at',
    )
    list_filter = ('status', 'priority', 'category', 'created_at')
    search_fields = ('ticket_id', 'title', 'description', 'customer__username', 'customer__email')
    readonly_fields = ('ticket_id', 'created_at', 'updated_at')
    list_per_page = 20

    fieldsets = (
        ('Ticket Identification', {
            'fields': ('ticket_id', 'created_at', 'updated_at')
        }),
        ('Issue Information', {
            'fields': ('customer', 'title', 'description', 'category')
        }),
        ('Triage & Assignment', {
            'fields': ('priority', 'status', 'assigned_to')
        }),
        ('Resolution', {
            'fields': ('resolution_notes',)
        }),
    )

    actions = ['mark_as_resolved', 'mark_as_in_progress', 'mark_as_closed']

    @admin.action(description="Mark selected tickets as In Progress")
    def mark_as_in_progress(self, request, queryset):
        queryset.update(status=Ticket.STATUS_IN_PROGRESS)

    @admin.action(description="Mark selected tickets as Resolved")
    def mark_as_resolved(self, request, queryset):
        queryset.update(status=Ticket.STATUS_RESOLVED)

    @admin.action(description="Mark selected tickets as Closed")
    def mark_as_closed(self, request, queryset):
        queryset.update(status=Ticket.STATUS_CLOSED)
