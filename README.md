# PocketPal — Personal Expense Tracker

PocketPal is a full-featured, web-based expense tracking application that helps users record their daily spending, manage recurring bills, and better understand their financial habits. Built with Flask and Python, backed by a PostgreSQL database on Supabase, and deployed on Render.

## Features

### User Authentication & Security
- **Registration & Login** — Secure account creation with real-time username availability checking and email uniqueness validation
- **Password Hashing** — All passwords are hashed using Werkzeug's `generate_password_hash` before storage
- **Password Validation** — Enforces minimum length, uppercase, lowercase, number, and special character requirements with live feedback during registration
- **Google OAuth** — Sign in with Google via Authlib; Google users can optionally set a password for dual login support
- **Forgot Password** — Email-based password reset with time-limited secure tokens via `itsdangerous`
- **Session Management** — Flask session-based authentication ensuring each user only accesses their own data

### Profile Management
- **Profile Picture** — Upload a custom profile photo (up to 2MB); falls back to initials avatar
- **Change Email** — Update account email with duplicate detection
- **Change Password** — Update password with full validation; Google users can set a password to enable username login
- **Custom Categories** — Add and delete personal spending categories beyond the defaults
- **Delete Account** — Permanently removes account and all associated data

### Expense Management
- **Add Expenses** — Log expenses with description, amount, date, category, and optional notes
- **Edit Expenses** — Inline row editing directly in the dashboard table
- **Delete Expenses** — Remove individual expense records with confirmation
- **Custom Categories** — Add a new category on the fly when logging an expense; saved permanently to your account
- **Notes Field** — Attach optional memo text to any expense

### Receipt Scanning
- **AI-Powered Scanning** — Upload or photograph a receipt using Tabscanner API to automatically extract merchant name, total amount, and date
- **Category Auto-Detection** — Merchant name is used to suggest the most appropriate spending category
- **Duplicate Detection** — Warns the user if a similar expense (same date, similar amount) already exists before adding
- **Preview & Edit** — Scanned data is shown in a review form before being saved, allowing corrections

### Recurring Bills
- **Add Recurring Bills** — Set up bills with name, amount, category, frequency (weekly, monthly, yearly), and start date
- **Automatic Processing** — Supabase pg_cron runs a PostgreSQL function daily at midnight to automatically add due bills as expenses and advance the next due date
- **Dashboard View** — Recurring bills are displayed in a scrollable table on the dashboard

### Budget Limits
- **Monthly Budget** — Set a monthly spending limit; a progress bar tracks how much of the budget has been used
- **Visual Alerts** — Progress bar turns red and a warning appears when the budget limit is reached or exceeded

### Analytics
- **Category Bar Chart** — Aggregated spending breakdown by category
- **Spending Trend Line Chart** — Daily expenditure plotted over time
- **User-Scoped Data** — All charts only show data belonging to the logged-in user

### Export & Download
- **CSV Export** — Download all expenses or a filtered subset as a CSV file
- **PDF Export** — Generate a formatted PDF report with a summary table and total
- **Filtered Export** — Filter by date range and category before downloading on a dedicated export page

### Dashboard
- **Stats Cards** — All-time total, current month spending, and top spending category
- **Monthly Average** — Shows average monthly spend once 2+ months of data exist; shows "First month of tracking" for new users
- **Filters** — Filter the expense table by start date, end date, and category
- **Running Total** — Displays the total for the currently filtered view

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | PostgreSQL via Supabase, SQLAlchemy ORM |
| Authentication | Werkzeug, Authlib (Google OAuth), itsdangerous |
| Email | Flask-Mail, Gmail SMTP |
| Receipt Scanning | Tabscanner API |
| Scheduling | Supabase pg_cron |
| PDF Generation | ReportLab |
| Frontend | HTML5, Tailwind CSS, Jinja2, Chart.js |
| Hosting | Render |

## Setup & Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/PocketPal.git
   cd PocketPal
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create an `a.env` file** with the following environment variables:
   ```
   DATABASE_URL=your_supabase_or_sqlite_url
   FLASK_SECRET_KEY=your_secret_key
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   MAIL_USERNAME=your_gmail_address
   MAIL_PASSWORD=your_gmail_app_password
   TABSCANNER_API_KEY=your_tabscanner_key
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the app** at `http://127.0.0.1:2030`

## Environment Variables (Render)

When deploying to Render, set the following environment variables in the dashboard:

- `DATABASE_URL`
- `FLASK_SECRET_KEY`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`
- `TABSCANNER_API_KEY`

## Database Migrations

The app automatically runs `ALTER TABLE` migrations on startup to add new columns to existing databases without data loss. New tables are created via `db.create_all()`.