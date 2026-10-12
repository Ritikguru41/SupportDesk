from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import HttpResponseForbidden

from .models import Ticket, UserProfile
from .forms import UserRegistrationForm, TicketCreateForm, TicketUpdateForm


def register_view(request):
    """
    User registration view supporting role assignment (Customer or Support Agent).
    """
    if request.user.is_authenticated:
        return redirect('tickets:dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to SupportDesk, {user.username}! Your account has been created.")
            return redirect('tickets:dashboard')
        else:
            messages.error(request, "Please correct the errors below to complete registration.")
    else:
        form = UserRegistrationForm()

    return render(request, 'registration/register.html', {'form': form})


def get_user_role(user):
    """Helper to safely determine user role."""
    if user.is_superuser or (hasattr(user, 'profile') and user.profile.is_admin):
        return 'admin'
    if hasattr(user, 'profile') and user.profile.is_agent:
        return 'agent'
    return 'customer'


@login_required
def dashboard_view(request):
    """
    Main dynamic dashboard aggregating support statistics via Django ORM.
    Customers see their personal ticket metrics.
    Agents and Admins see team-wide or assigned operations.
    """
    user = request.user
    role = get_user_role(user)

    # Base queryset based on role
    if role == 'customer':
        base_qs = Ticket.objects.filter(customer=user)
    elif role == 'agent' and request.GET.get('view') == 'assigned':
        base_qs = Ticket.objects.filter(assigned_to=user)
    else:
        base_qs = Ticket.objects.all()

    # Dynamic metrics calculated via ORM aggregation
    stats = {
        'total': base_qs.count(),
        'open': base_qs.filter(status=Ticket.STATUS_OPEN).count(),
        'in_progress': base_qs.filter(status=Ticket.STATUS_IN_PROGRESS).count(),
        'resolved': base_qs.filter(status=Ticket.STATUS_RESOLVED).count(),
        'closed': base_qs.filter(status=Ticket.STATUS_CLOSED).count(),
    }

    # Priority breakdown
    priority_counts = (
        base_qs.values('priority')
        .annotate(count=Count('id'))
        .order_by('priority')
    )
    priority_dict = {p[0]: 0 for p in Ticket.PRIORITY_CHOICES}
    for item in priority_counts:
        priority_dict[item['priority']] = item['count']

    # Category breakdown
    category_counts = (
        base_qs.values('category')
        .annotate(count=Count('id'))
        .order_by('category')
    )
    category_dict = {c[0]: 0 for c in Ticket.CATEGORY_CHOICES}
    for item in category_counts:
        category_dict[item['category']] = item['count']

    # Recently created tickets (last 5)
    recent_tickets = base_qs.select_related('customer', 'assigned_to')[:5]

    context = {
        'role': role,
        'stats': stats,
        'priority_dict': priority_dict,
        'category_dict': category_dict,
        'recent_tickets': recent_tickets,
        'active_tab': 'dashboard',
        'view_mode': request.GET.get('view', 'all'),
    }
    return render(request, 'tickets/dashboard.html', context)


@login_required
def ticket_list_view(request):
    """
    Searchable, filterable, and sortable ticket directory with pagination.
    """
    user = request.user
    role = get_user_role(user)

    # Base role-filtered queryset
    if role == 'customer':
        queryset = Ticket.objects.filter(customer=user)
    else:
        queryset = Ticket.objects.all()

    # Query search (title, ticket_id, description)
    q = request.GET.get('q', '').strip()
    if q:
        queryset = queryset.filter(
            Q(title__icontains=q) |
            Q(ticket_id__icontains=q) |
            Q(description__icontains=q) |
            Q(customer__username__icontains=q)
        )

    # Status filter
    status_filter = request.GET.get('status', '').strip()
    if status_filter and status_filter in dict(Ticket.STATUS_CHOICES):
        queryset = queryset.filter(status=status_filter)

    # Priority filter
    priority_filter = request.GET.get('priority', '').strip()
    if priority_filter and priority_filter in dict(Ticket.PRIORITY_CHOICES):
        queryset = queryset.filter(priority=priority_filter)

    # Category filter
    category_filter = request.GET.get('category', '').strip()
    if category_filter and category_filter in dict(Ticket.CATEGORY_CHOICES):
        queryset = queryset.filter(category=category_filter)

    # Assignment filter for agents/admins
    assigned_filter = request.GET.get('assigned', '').strip()
    if role in ('agent', 'admin'):
        if assigned_filter == 'me':
            queryset = queryset.filter(assigned_to=user)
        elif assigned_filter == 'unassigned':
            queryset = queryset.filter(assigned_to__isnull=True)

    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    valid_sorts = ['-created_at', 'created_at', 'priority', '-priority', 'status', 'title']
    if sort_by in valid_sorts:
        queryset = queryset.order_by(sort_by)
    else:
        queryset = queryset.order_by('-created_at')

    queryset = queryset.select_related('customer', 'assigned_to')

    # Pagination: 10 per page
    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'role': role,
        'q': q,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'category_filter': category_filter,
        'assigned_filter': assigned_filter,
        'sort_by': sort_by,
        'status_choices': Ticket.STATUS_CHOICES,
        'priority_choices': Ticket.PRIORITY_CHOICES,
        'category_choices': Ticket.CATEGORY_CHOICES,
        'active_tab': 'tickets',
        'total_count': paginator.count,
    }
    return render(request, 'tickets/ticket_list.html', context)


@login_required
def ticket_create_view(request):
    """
    Create a new support ticket.
    """
    if request.method == 'POST':
        form = TicketCreateForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.customer = request.user
            ticket.status = Ticket.STATUS_OPEN
            ticket.save()
            messages.success(request, f"Ticket {ticket.ticket_id} created successfully!")
            return redirect('tickets:ticket_detail', ticket_id=ticket.ticket_id)
        else:
            messages.error(request, "Please resolve the errors below before submitting.")
    else:
        form = TicketCreateForm()

    return render(request, 'tickets/ticket_form.html', {
        'form': form,
        'is_edit': False,
        'active_tab': 'new_ticket'
    })


@login_required
def ticket_detail_view(request, ticket_id):
    """
    View ticket details with status change panel for agents.
    Enforces authorization: Customers can ONLY view their own tickets.
    """
    ticket = get_object_or_404(Ticket.objects.select_related('customer', 'assigned_to'), ticket_id=ticket_id)
    role = get_user_role(request.user)

    # Authorization Check
    if role == 'customer' and ticket.customer != request.user:
        messages.error(request, "You are not authorized to view this support ticket.")
        return redirect('tickets:ticket_list')

    # Handle inline quick status / note updates from support agents
    if request.method == 'POST' and role in ('agent', 'admin'):
        action = request.POST.get('action')
        if action == 'update_status':
            new_status = request.POST.get('status')
            if new_status in dict(Ticket.STATUS_CHOICES):
                ticket.status = new_status
                messages.success(request, f"Ticket status updated to {new_status}.")

        elif action == 'assign_agent':
            agent_id = request.POST.get('assigned_to')
            if agent_id:
                agent_user = get_object_or_404(UserProfile.objects.filter(role__in=['agent', 'admin']).values_list('user', flat=True), pk=agent_id) if agent_id else None
                # or direct user lookup:
                from django.contrib.auth.models import User
                agent_user = User.objects.filter(pk=agent_id).first()
                ticket.assigned_to = agent_user
                messages.success(request, f"Ticket assigned to {agent_user.username if agent_user else 'None'}.")
            else:
                ticket.assigned_to = None
                messages.info(request, "Ticket is now unassigned.")

        elif action == 'add_resolution':
            notes = request.POST.get('resolution_notes', '').strip()
            ticket.resolution_notes = notes
            new_status = request.POST.get('status')
            if new_status in dict(Ticket.STATUS_CHOICES):
                ticket.status = new_status
            messages.success(request, "Resolution notes saved successfully.")

        ticket.save()
        return redirect('tickets:ticket_detail', ticket_id=ticket.ticket_id)

    # Available agents for assignment dropdown
    from django.contrib.auth.models import User
    agents = User.objects.filter(
        Q(profile__role__in=['agent', 'admin']) | Q(is_staff=True) | Q(is_superuser=True)
    ).distinct()

    context = {
        'ticket': ticket,
        'role': role,
        'agents': agents,
        'status_choices': Ticket.STATUS_CHOICES,
        'active_tab': 'tickets',
    }
    return render(request, 'tickets/ticket_detail.html', context)


@login_required
def ticket_update_view(request, ticket_id):
    """
    Update ticket details.
    Customers can update details if not closed.
    Agents & Admins can update status, priority, category, assignment, and notes.
    """
    ticket = get_object_or_404(Ticket, ticket_id=ticket_id)
    role = get_user_role(request.user)

    # Authorization Check
    if role == 'customer':
        if ticket.customer != request.user:
            messages.error(request, "You cannot edit tickets that do not belong to you.")
            return redirect('tickets:ticket_list')
        if ticket.status == Ticket.STATUS_CLOSED:
            messages.warning(request, "Closed tickets cannot be edited.")
            return redirect('tickets:ticket_detail', ticket_id=ticket.ticket_id)

    if request.method == 'POST':
        form = TicketUpdateForm(request.POST, instance=ticket, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Ticket {ticket.ticket_id} updated successfully!")
            return redirect('tickets:ticket_detail', ticket_id=ticket.ticket_id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = TicketUpdateForm(instance=ticket, user=request.user)

    return render(request, 'tickets/ticket_form.html', {
        'form': form,
        'ticket': ticket,
        'is_edit': True,
        'active_tab': 'tickets'
    })


@login_required
def ticket_delete_view(request, ticket_id):
    """
    Delete ticket.
    Permitted for Admins, or Customers if ticket is still Open.
    Requires POST method for CSRF protection against accidental/malicious deletion.
    """
    ticket = get_object_or_404(Ticket, ticket_id=ticket_id)
    role = get_user_role(request.user)

    # Permissions
    can_delete = (role == 'admin') or (role == 'customer' and ticket.customer == request.user and ticket.status == Ticket.STATUS_OPEN)

    if not can_delete:
        messages.error(request, "You do not have permission to delete this ticket.")
        return redirect('tickets:ticket_detail', ticket_id=ticket.ticket_id)

    if request.method == 'POST':
        tid = ticket.ticket_id
        ticket.delete()
        messages.success(request, f"Ticket {tid} was deleted successfully.")
        return redirect('tickets:ticket_list')

    # Confirmation view if accessed via GET
    return render(request, 'tickets/ticket_confirm_delete.html', {'ticket': ticket})
