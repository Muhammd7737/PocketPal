# PocketPall Expense Tracker

PocketPall is a web-based expense tracking application that helps users record their daily spending and better understand their financial habits. The application is built using Flask and Python, with SQL used for storing and managing expense data.

The goal of this project was to create a simple system where users can log expenses while also seeing useful insights through visual analytics. Instead of just storing transactions, the application processes the data and presents spending patterns through graphs.

## Core Functionality

### User Authentication and Security
* **Account Management:** Users can create personal accounts and manage their profiles.
* **Secure Sessions:** Implementation of Flask-Login ensures that user data is isolated and protected.
* **Data Privacy:** Each user only has access to their own recorded financial data through relational database constraints.

### Expense Management
* **CRUD Operations:** Full capability to create, read, update, and delete expense records.
* **Detailed Logging:** Users can categorize expenses and add specific timestamps to each transaction.
* **Filtering and Search:** Built-in functionality to sort through past transactions to find specific spending events or trends.

### Data Analytics Dashboard
* **Categorical Analysis:** A bar chart interface that aggregates spending by category to show where the largest expenses occur.
* **Trend Visualization:** Line graphs generated via Matplotlib and Seaborn to track spending spikes over time.
* **Data Processing:** Utilization of Pandas for efficient data cleaning and aggregation of SQL records.

## Technologies Used

* **Backend:** Python, Flask
* **Database:** SQLite with SQLAlchemy ORM
* **Authentication:** Flask-Login
* **Data Analysis:** Pandas, NumPy
* **Visualization:** Matplotlib, Seaborn
* **Frontend:** HTML5, CSS3, Jinja2 Templates

## Installation and Setup

1. **Clone the repository:**
2. **Ensure you have Python3.x installed**
3. **Create a virtual environment and activate it**
4. **Install the required packages using: pip install -r requirements.txt**
5. **Initialize the database and run the application using: python app.py**
6. **Access the application via localhost:5000 in your web browser**