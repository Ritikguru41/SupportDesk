"""
Management command to seed initial roles, test users, and realistic tickets for SupportDesk.
Usage: python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tickets.models import Ticket, UserProfile


class Command(BaseCommand):
    help = "Seeds test users (Admin, Support Agent, Customer) and sample tickets."

    def handle(self, *args, **options):
        self.stdout.write("Seeding SupportDesk test accounts and ticket records...")

        # 1. Administrator
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@supportdesk.internal',
                'first_name': 'Eleanor',
                'last_name': 'Vance',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('Admin@12345')
            admin_user.save()
            admin_profile, _ = UserProfile.objects.get_or_create(user=admin_user)
            admin_profile.role = UserProfile.ROLE_ADMIN
            admin_profile.save()
            self.stdout.write(self.style.SUCCESS("Created Administrator: admin / Admin@12345"))
        else:
            self.stdout.write("Administrator 'admin' already exists.")

        # 2. Support Agent
        agent_user, created = User.objects.get_or_create(
            username='agent_sarah',
            defaults={
                'email': 'sarah.agent@supportdesk.internal',
                'first_name': 'Sarah',
                'last_name': 'Connor',
                'is_staff': True,
            }
        )
        if created:
            agent_user.set_password('Agent@12345')
            agent_user.save()
            agent_profile, _ = UserProfile.objects.get_or_create(user=agent_user)
            agent_profile.role = UserProfile.ROLE_AGENT
            agent_profile.save()
            self.stdout.write(self.style.SUCCESS("Created Support Agent: agent_sarah / Agent@12345"))
        else:
            self.stdout.write("Support Agent 'agent_sarah' already exists.")

        # 3. Customer
        customer_user, created = User.objects.get_or_create(
            username='customer_alex',
            defaults={
                'email': 'alex.client@company.com',
                'first_name': 'Alex',
                'last_name': 'Mercer',
            }
        )
        if created:
            customer_user.set_password('Customer@12345')
            customer_user.save()
            customer_profile, _ = UserProfile.objects.get_or_create(user=customer_user)
            customer_profile.role = UserProfile.ROLE_CUSTOMER
            customer_profile.save()
            self.stdout.write(self.style.SUCCESS("Created Customer: customer_alex / Customer@12345"))
        else:
            self.stdout.write("Customer 'customer_alex' already exists.")

        # 4. Sample Support Tickets
        sample_tickets = [
            {
                'title': 'VPN connection drops intermittently every 15 minutes',
                'description': 'Whenever I connect to the enterprise VPN from the remote office, the tunnel drops abruptly with error code TLS-104. Steps taken: reinstalled client, flushed DNS cache.',
                'category': Ticket.CAT_TECHNICAL,
                'priority': Ticket.PRIORITY_HIGH,
                'status': Ticket.STATUS_IN_PROGRESS,
                'customer': customer_user,
                'assigned_to': agent_user,
                'resolution_notes': 'Investigating gateway NAT timeout settings on the perimeter firewall.',
            },
            {
                'title': 'Discrepancy in Q3 invoice VAT calculation',
                'description': 'Our monthly billing receipt #INV-9821 reflects a 20% VAT rate instead of the exempt rate agreed upon under our corporate master service agreement.',
                'category': Ticket.CAT_BILLING,
                'priority': Ticket.PRIORITY_MEDIUM,
                'status': Ticket.STATUS_OPEN,
                'customer': customer_user,
                'assigned_to': None,
                'resolution_notes': '',
            },
            {
                'title': 'Production database latency spike on payment gateway',
                'description': 'Payment webhooks are encountering 504 Gateway Timeouts. Database read replicas are reporting 98% CPU saturation during peak transaction checkout window.',
                'category': Ticket.CAT_TECHNICAL,
                'priority': Ticket.PRIORITY_CRITICAL,
                'status': Ticket.STATUS_RESOLVED,
                'customer': customer_user,
                'assigned_to': agent_user,
                'resolution_notes': 'Identified unindexed foreign key in checkout_order table. Applied schema index migration and rebooted connection pooling daemon.',
            },
            {
                'title': 'Requesting 2-Factor Authentication reset for SSO login',
                'description': 'I replaced my mobile phone and lost access to the Google Authenticator app for my primary enterprise login credentials.',
                'category': Ticket.CAT_ACCOUNT,
                'priority': Ticket.PRIORITY_HIGH,
                'status': Ticket.STATUS_CLOSED,
                'customer': customer_user,
                'assigned_to': agent_user,
                'resolution_notes': 'Verified employee identity through internal manager confirmation call. Cleared MFA token and issued temporary one-time recovery key.',
            },
            {
                'title': 'Need additional seats for Analytics reporting addon',
                'description': 'Our department is onboarding 4 new data analysts next Monday and we require dashboard read permissions for their accounts.',
                'category': Ticket.CAT_ACCOUNT,
                'priority': Ticket.PRIORITY_LOW,
                'status': Ticket.STATUS_OPEN,
                'customer': customer_user,
                'assigned_to': None,
                'resolution_notes': '',
            },
            {
                'title': 'Email notification delivery delay on ticket updates',
                'description': 'Notifications for ticket status changes are arriving 2 to 3 hours after the action was logged in the dashboard.',
                'category': Ticket.CAT_TECHNICAL,
                'priority': Ticket.PRIORITY_MEDIUM,
                'status': Ticket.STATUS_IN_PROGRESS,
                'customer': customer_user,
                'assigned_to': agent_user,
                'resolution_notes': 'RabbitMQ email worker queue accumulated a backlog; worker concurrency increased from 2 to 8 threads.',
            },
        ]

        created_count = 0
        for data in sample_tickets:
            if not Ticket.objects.filter(title=data['title']).exists():
                Ticket.objects.create(**data)
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Seeding finished. {created_count} sample tickets added to MySQL."))
