
# Reading Lab

Reading Lab is a Django web application for exploring and managing personal reading histories imported from Goodreads.

Users can create accounts, import their reading history from a CSV file, explore reading statistics, search and filter their library, edit book information, and store private reading notes.

## Technologies

- Python 3
- Django
- SQLite
- HTML and CSS
- JavaScript
- Cryptography (for the documented encryption fix)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Carla1115/reading-lab.git
cd reading-lab
```

### 2. Create and activate a virtual environment

On macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows:

```powershell
py -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root containing:

```dotenv
DJANGO_SECRET_KEY='YOUR_GENERATED_DJANGO_SECRET_KEY'
READING_LAB_FERNET_KEY='YOUR_GENERATED_FERNET_KEY'
```

Generate your own values using Python:

```python
from django.core.management.utils import get_random_secret_key
from cryptography.fernet import Fernet

print("Django key:", get_random_secret_key())
print("Fernet key:", Fernet.generate_key().decode())
```

Copy each generated value into the corresponding variable in `.env`.

Never commit `.env` or share these keys.

### 5. Set up the database

```bash
python manage.py migrate
```

### 6. Start the development server

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/ in your browser.

Create an account to begin using Reading Lab. You can then import a Goodreads CSV export to explore your reading history.

## Security vulnerabilities

This project was created for the University of Helsinki Cyber Security Base MOOC.

It intentionally contains five security vulnerabilities corresponding to different OWASP Top 10:2021 categories.

### FLAW 1 — A01: Broken Access Control

A user can modify another user's reading record by changing a submitted record identifier.

Location: `analytics/views.py`

The commented fix restricts record lookup to the authenticated user.

### FLAW 2 — A03: Injection

The library search constructs an SQL query using unsanitized user input.

Location: `analytics/views.py`

The commented fix uses Django ORM filtering instead of SQL string interpolation.

### FLAW 3 — A07: Identification and Authentication Failures

The login form accepts repeated failed authentication attempts without rate limiting.

Location: `analytics/views.py`

The commented fix introduces a temporary lockout after repeated failed attempts.

### FLAW 4 — A02: Cryptographic Failures

Private reading notes are stored in plaintext.

Locations: `analytics/models.py` and `analytics/encrypted_fields.py`

The commented fix uses Fernet encryption to protect stored notes.

### FLAW 5 — A09: Security Logging and Monitoring Failures

The application does not register its dedicated authentication security event handlers.

Locations: `analytics/apps.py` and `analytics/security_signals.py`

The commented fix enables logging of failed authentication attempts and suspicious login activity.

## How to review the fixes

The vulnerable implementations are active by default.

The corresponding fixes are provided as commented code or separate helper modules. Review the comments in the indicated source files to understand how each fix should be activated.

## Security notice

This application is intentionally vulnerable and is intended exclusively for educational use in a local testing environment.

Do not deploy it to a public server or use it with sensitive personal information.

The repository does not include users' private CSV exports, local databases, environment variables, or security logs.
