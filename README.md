# SupportDesk – Customer Support Management System

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://www.djangoproject.com/)
[![Database](https://img.shields.io/badge/Database-MySQL%208.0-orange.svg)](https://www.mysql.com/)
[![Frontend](https://img.shields.io/badge/Frontend-HTML5%20%7C%20CSS3%20%7C%20Vanilla%20JS-purple.svg)]()
[![Tests](https://img.shields.io/badge/Tests-8%20Passed-brightgreen.svg)]()

**SupportDesk** is a production-grade, full-stack Customer Support Management web application designed and built for enterprise ticket resolution workflows. Developed using **Python**, **Django ORM**, and **MySQL**, with a bespoke, zero-dependency **HTML5 / CSS3 / Vanilla JavaScript** frontend.

---

## 🌟 Key Features

### 1. Role-Based Access Control (RBAC)
- **Customer**: Raise new support tickets, view own submitted tickets, track status in real-time, edit open tickets.
- **Support Agent**: Triage incoming tickets, assign tickets to agents, update lifecycle status, write internal/external resolution notes.
- **Administrator**: Full system visibility across all users, tickets, assignments, system-wide metrics, and Django administration access.

### 2. Operational Analytics Dashboard
- Dynamic summary cards: **Total**, **Open**, **In Progress**, **Resolved**, and **Closed** tickets calculated using optimized Django ORM aggregations.
- Interactive **Priority Breakdown** (Low, Medium, High, Critical) with progress bars.
- **Category Distribution** (Technical, Account, Billing, Other).
- **Recent Tickets Feed** with live status pill indicators.

### 3. Ticket Lifecycle & Management
- Auto-generation of human-readable ticket identifiers (`TIC-1001`, `TIC-1002`).
- Real-time search across ticket IDs, titles, descriptions, and customer usernames.
- Multi-parameter filtering by **Status**, **Priority**, **Category**, and **Agent Assignment**.
- Multi-attribute sorting by newest, oldest, priority, and status.
- Pagination controls (10 tickets per page).
- Secure deletion confirmation workflow protected by CSRF and permission validation.

### 4. Custom SaaS Design System
- Modern sidebar navigation with active route highlights and user avatar.
- Color-coded priority and status badges.
- Toast notifications with auto-dismissal.
- Responsive mobile drawer layout with touch-friendly navigation.
- Zero third-party CSS/JS frameworks (no Bootstrap, no Tailwind, no React).

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | Django 5.2 (Python 3.12) |
| **Database** | MySQL 8.0 (MySQL Community Server) |
| **Database Driver** | PyMySQL 1.1 + Cryptography (`caching_sha2_password` native support) |
| **ORM** | Django Object-Relational Mapping (ORM) |
| **Frontend Structure** | Semantic HTML5 |
| **Styling** | Custom CSS3 Design System (CSS Variables, Flexbox, CSS Grid) |
| **Client-Side Scripting** | Vanilla JavaScript (ES6+) |
| **Testing** | Django TestCase (`python manage.py test`) |

---

## 🚀 Quick Start Guide (Windows PowerShell)

### Step 1: Open Terminal in the Project Directory
```powershell
cd "c:\Users\Sandhya Vishwakarma\OneDrive\Desktop\supportDesk"
```

### Step 2: Activate the Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```

### Step 3: Configure Environment Variables
Verify your [.env](file:///.env) file:
```env
SECRET_KEY=django-insecure-k39!m8x$b(supportdesk-placement-grade-sys2026!
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

DB_ENGINE=mysql
DB_NAME=supportdesk_db
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3307
```

### Step 4: Run Migrations (Already completed)
```powershell
python manage.py migrate
```

### Step 5: (Optional) Seed Test Data
Populates sample roles, accounts, and 6 realistic support tickets:
```powershell
python manage.py seed_data
```

### Step 6: Start the Development Server
```powershell
python manage.py runserver
```

Open your browser at:
**[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

## 👥 Pre-Configured Test Accounts

| Role | Username | Password | Access Capabilities |
|---|---|---|---|
| **Administrator** | `admin` | `Admin@12345` | Global view, ticket deletion, triage, [Django Admin](http://127.0.0.1:8000/admin/) |
| **Support Agent** | `agent_sarah` | `Agent@12345` | Triage panel, status change, agent assignment, resolution notes |
| **Customer** | `customer_alex` | `Customer@12345` | Personal dashboard, ticket creation, view own tickets |

---

## 🧪 Running Automated Tests

Run the test suite verifying authentication, access scoping, and ORM metrics:

```powershell
python manage.py test
```

Expected output:
```text
Found 8 test(s).
Creating test database for alias 'default'...
........
----------------------------------------------------------------------
Ran 8 tests in 0.8s

OK
Destroying test database for alias 'default'...
```

---

## 💡 Placement Interview Reference: Architecture & Concepts

1. **Django MVT Pattern (Model-View-Template)**:
   - **Model (`Ticket`, `UserProfile`)**: Encapsulates database schema, constraints, choices, and custom `save()` ticket ID logic.
   - **View (`views.py`)**: Implements request handling, permission checks, ORM query filtering, and form handling.
   - **Template (`templates/`)**: Renders HTML dynamically with context data, badge mappings, and CSRF protection.

2. **Signals (`post_save`)**:
   Used to automatically create or synchronize a `UserProfile` whenever a new `User` instance is registered.

3. **Query Optimization (`select_related`)**:
   In `ticket_list_view` and `dashboard_view`, `select_related('customer', 'assigned_to')` performs SQL `JOIN`s, avoiding the $N+1$ database query bottleneck.

4. **PyMySQL Monkeypatching**:
   In `config/__init__.py`, `pymysql.install_as_MySQLdb()` enables seamless Python 3.12 MySQL support on Windows without requiring Microsoft C++ Build Tools compilation.
