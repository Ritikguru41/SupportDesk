from django import forms
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Ticket, UserProfile


class UserRegistrationForm(forms.ModelForm):
    """
    Form for registering new users with password confirmation and role assignment.
    """
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Choose a strong password', 'class': 'form-control'}),
        label="Password",
        min_length=8,
        help_text="Must be at least 8 characters long."
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Repeat your password', 'class': 'form-control'}),
        label="Confirm Password"
    )
    role = forms.ChoiceField(
        choices=[
            (UserProfile.ROLE_CUSTOMER, 'Customer (Create & track tickets)'),
            (UserProfile.ROLE_AGENT, 'Support Agent (Manage & resolve tickets)'),
        ],
        initial=UserProfile.ROLE_CUSTOMER,
        label="Account Role",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Enter unique username', 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'placeholder': 'name@example.com', 'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'First name', 'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last name', 'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError("Email is required.")
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("A user with that email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            role = self.cleaned_data.get('role', UserProfile.ROLE_CUSTOMER)
            # UserProfile is created via post_save signal, update its role
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.save()
        return user


class TicketCreateForm(forms.ModelForm):
    """
    Form for customers and users to create a new support ticket.
    """
    class Meta:
        model = Ticket
        fields = ('title', 'category', 'priority', 'description')
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Brief summary of the issue (e.g. Cannot reset password)',
                'class': 'form-control',
                'maxlength': '200'
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'placeholder': 'Provide detailed steps to reproduce the issue, expected outcome, and error messages...',
                'class': 'form-control',
                'rows': 5
            }),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if len(title) < 5:
            raise ValidationError("Title must be at least 5 characters long.")
        return title

    def clean_description(self):
        desc = self.cleaned_data.get('description', '').strip()
        if len(desc) < 15:
            raise ValidationError("Please provide a detailed description (at least 15 characters).")
        return desc


class TicketUpdateForm(forms.ModelForm):
    """
    Role-aware ticket update form.
    Agents & Admins can change status, assigned agent, and resolution notes.
    Customers can update title, description, category, and priority (if not closed).
    """
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        is_staff_or_agent = (
            user and (user.is_superuser or (hasattr(user, 'profile') and user.profile.is_agent))
        )

        # Populate agent queryset for assignment dropdown
        agents = User.objects.filter(
            models.Q(profile__role__in=[UserProfile.ROLE_AGENT, UserProfile.ROLE_ADMIN]) |
            models.Q(is_staff=True) |
            models.Q(is_superuser=True)
        ).distinct()
        self.fields['assigned_to'].queryset = agents

        if not is_staff_or_agent:
            # Customers cannot change status, assigned_to or resolution_notes
            self.fields.pop('status', None)
            self.fields.pop('assigned_to', None)
            self.fields.pop('resolution_notes', None)

    class Meta:
        model = Ticket
        fields = ('title', 'category', 'priority', 'status', 'assigned_to', 'description', 'resolution_notes')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'resolution_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add details on how this issue was resolved or current investigation findings...'
            }),
        }
