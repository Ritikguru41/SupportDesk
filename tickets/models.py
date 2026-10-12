import uuid
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """
    Extends Django's User model with role-based access control.
    Roles:
      - customer: Can create and view own tickets
      - agent: Can view assigned/all tickets, update status, add resolution notes
      - admin: Full administrative access across all tickets and assignments
    """
    ROLE_CUSTOMER = 'customer'
    ROLE_AGENT = 'agent'
    ROLE_ADMIN = 'admin'

    ROLE_CHOICES = [
        (ROLE_CUSTOMER, 'Customer'),
        (ROLE_AGENT, 'Support Agent'),
        (ROLE_ADMIN, 'Administrator'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CUSTOMER)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def is_customer(self):
        return self.role == self.ROLE_CUSTOMER and not self.user.is_superuser

    @property
    def is_agent(self):
        return self.role == self.ROLE_AGENT or self.user.is_staff or self.user.is_superuser

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN or self.user.is_superuser


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Signal receiver to create or update UserProfile automatically on User save.
    """
    if created:
        role = UserProfile.ROLE_ADMIN if instance.is_superuser else UserProfile.ROLE_CUSTOMER
        UserProfile.objects.create(user=instance, role=role)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            role = UserProfile.ROLE_ADMIN if instance.is_superuser else UserProfile.ROLE_CUSTOMER
            UserProfile.objects.create(user=instance, role=role)


class Ticket(models.Model):
    """
    Core Support Ticket model tracking customer issues, priority, lifecycle status,
    and agent resolution notes.
    """
    # Category Choices
    CAT_TECHNICAL = 'Technical'
    CAT_ACCOUNT = 'Account'
    CAT_BILLING = 'Billing'
    CAT_OTHER = 'Other'

    CATEGORY_CHOICES = [
        (CAT_TECHNICAL, 'Technical'),
        (CAT_ACCOUNT, 'Account'),
        (CAT_BILLING, 'Billing'),
        (CAT_OTHER, 'Other'),
    ]

    # Priority Choices
    PRIORITY_LOW = 'Low'
    PRIORITY_MEDIUM = 'Medium'
    PRIORITY_HIGH = 'High'
    PRIORITY_CRITICAL = 'Critical'

    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_CRITICAL, 'Critical'),
    ]

    # Status Choices
    STATUS_OPEN = 'Open'
    STATUS_IN_PROGRESS = 'In Progress'
    STATUS_RESOLVED = 'Resolved'
    STATUS_CLOSED = 'Closed'

    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_CLOSED, 'Closed'),
    ]

    ticket_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        db_index=True,
        help_text="Unique human-readable ticket reference (e.g. TIC-10023)"
    )
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tickets_created',
        help_text="Customer who submitted the ticket"
    )
    title = models.CharField(max_length=200, help_text="Short description of the issue")
    description = models.TextField(help_text="Detailed issue description")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CAT_TECHNICAL)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets',
        help_text="Support agent handling the ticket"
    )
    resolution_notes = models.TextField(blank=True, default='', help_text="Notes detailing the fix or resolution")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['created_at']),
            models.Index(fields=['ticket_id']),
        ]
        verbose_name = 'Support Ticket'
        verbose_name_plural = 'Support Tickets'

    def __str__(self):
        return f"{self.ticket_id} - {self.title} ({self.status})"

    def save(self, *args, **kwargs):
        """
        Generate sequential/unique human-readable ticket ID upon first creation.
        """
        if not self.ticket_id:
            last_ticket = Ticket.objects.order_by('-id').first()
            if last_ticket and last_ticket.id:
                new_num = last_ticket.id + 1
            else:
                new_num = 1001
            candidate_id = f"TIC-{new_num}"
            while Ticket.objects.filter(ticket_id=candidate_id).exists():
                new_num += 1
                candidate_id = f"TIC-{new_num}"
            self.ticket_id = candidate_id
        super().save(*args, **kwargs)
