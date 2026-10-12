from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from tickets.models import Ticket, UserProfile
from tickets.forms import TicketCreateForm, UserRegistrationForm


class SupportDeskTests(TestCase):
    """
    Comprehensive automated test suite covering:
    - Authentication and Role-based Access Control
    - Ticket CRUD lifecycle
    - Permissions and Data Scoping (Customer vs Agent vs Admin)
    - Form Validation
    - Dashboard ORM aggregations
    """

    def setUp(self):
        # 1. Setup Users with different roles
        self.customer = User.objects.create_user(
            username='cust_jane',
            email='jane@client.com',
            password='Password123!'
        )
        # Profile is created via signal
        self.customer.profile.role = UserProfile.ROLE_CUSTOMER
        self.customer.profile.save()

        self.other_customer = User.objects.create_user(
            username='cust_bob',
            email='bob@client.com',
            password='Password123!'
        )
        self.other_customer.profile.role = UserProfile.ROLE_CUSTOMER
        self.other_customer.profile.save()

        self.agent = User.objects.create_user(
            username='agent_tom',
            email='tom@supportdesk.internal',
            password='Password123!'
        )
        self.agent.profile.role = UserProfile.ROLE_AGENT
        self.agent.profile.save()

        self.admin_user = User.objects.create_superuser(
            username='admin_super',
            email='super@supportdesk.internal',
            password='Password123!'
        )

        # 2. Setup initial test tickets
        self.ticket1 = Ticket.objects.create(
            customer=self.customer,
            title='Cannot access billing portal',
            description='Getting 403 Forbidden on the invoices tab after account renewal.',
            category=Ticket.CAT_BILLING,
            priority=Ticket.PRIORITY_HIGH,
            status=Ticket.STATUS_OPEN
        )

        self.client = Client()

    def test_ticket_id_auto_generation(self):
        """Ticket model should generate unique human-readable ticket_id on save."""
        self.assertTrue(self.ticket1.ticket_id.startswith('TIC-'))
        ticket2 = Ticket.objects.create(
            customer=self.customer,
            title='Second ticket test',
            description='Second ticket detailed description text here.',
            category=Ticket.CAT_TECHNICAL,
            priority=Ticket.PRIORITY_LOW,
            status=Ticket.STATUS_OPEN
        )
        self.assertNotEqual(self.ticket1.ticket_id, ticket2.ticket_id)

    def test_login_required_protection(self):
        """Unauthenticated requests must be redirected to login page."""
        response = self.client.get(reverse('tickets:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

        response = self.client.get(reverse('tickets:ticket_list'))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('tickets:ticket_create'))
        self.assertEqual(response.status_code, 302)

    def test_customer_ticket_visibility_scoping(self):
        """A customer must only see their own tickets, not tickets of other customers."""
        ticket_bob = Ticket.objects.create(
            customer=self.other_customer,
            title='Bob private ticket issue',
            description='Bob private confidential details here.',
            category=Ticket.CAT_ACCOUNT,
            priority=Ticket.PRIORITY_LOW,
            status=Ticket.STATUS_OPEN
        )

        # Login as Jane
        self.client.login(username='cust_jane', password='Password123!')
        response = self.client.get(reverse('tickets:ticket_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.ticket1.ticket_id)
        self.assertNotContains(response, ticket_bob.ticket_id)

        # Jane should be denied access to Bob's ticket detail
        response = self.client.get(reverse('tickets:ticket_detail', args=[ticket_bob.ticket_id]))
        self.assertEqual(response.status_code, 302)  # Redirects with error message

    def test_agent_can_view_all_tickets(self):
        """Support agents must be able to view tickets across customers."""
        self.client.login(username='agent_tom', password='Password123!')
        response = self.client.get(reverse('tickets:ticket_detail', args=[self.ticket1.ticket_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.ticket1.title)

    def test_ticket_creation_flow(self):
        """Authenticated customer can successfully create a new ticket."""
        self.client.login(username='cust_jane', password='Password123!')
        response = self.client.post(reverse('tickets:ticket_create'), {
            'title': 'Email sync failing',
            'category': Ticket.CAT_TECHNICAL,
            'priority': Ticket.PRIORITY_MEDIUM,
            'description': 'Microsoft Exchange connector fails to synchronize calendar events.'
        })
        self.assertEqual(response.status_code, 302)
        new_ticket = Ticket.objects.filter(title='Email sync failing').first()
        self.assertIsNotNone(new_ticket)
        self.assertEqual(new_ticket.customer, self.customer)
        self.assertEqual(new_ticket.status, Ticket.STATUS_OPEN)

    def test_agent_status_and_resolution_update(self):
        """Support agent can update status and add resolution notes via action panel."""
        self.client.login(username='agent_tom', password='Password123!')
        response = self.client.post(
            reverse('tickets:ticket_detail', args=[self.ticket1.ticket_id]),
            {
                'action': 'add_resolution',
                'status': Ticket.STATUS_RESOLVED,
                'resolution_notes': 'Granted missing billing permission role to user account.'
            }
        )
        self.assertEqual(response.status_code, 302)
        self.ticket1.refresh_from_db()
        self.assertEqual(self.ticket1.status, Ticket.STATUS_RESOLVED)
        self.assertEqual(self.ticket1.resolution_notes, 'Granted missing billing permission role to user account.')

    def test_ticket_form_validation(self):
        """Form rejects short titles or descriptions."""
        form = TicketCreateForm(data={
            'title': 'Bad',
            'category': Ticket.CAT_TECHNICAL,
            'priority': Ticket.PRIORITY_LOW,
            'description': 'Short'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
        self.assertIn('description', form.errors)

    def test_dashboard_statistics_calculation(self):
        """Dashboard accurately computes counts via ORM aggregation."""
        self.client.login(username='admin_super', password='Password123!')
        response = self.client.get(reverse('tickets:dashboard'))
        self.assertEqual(response.status_code, 200)
        stats = response.context['stats']
        self.assertGreaterEqual(stats['total'], 1)
        self.assertGreaterEqual(stats['open'], 1)
