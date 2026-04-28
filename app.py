#from unicodedata import category
from dotenv import load_dotenv
from flask import Flask, render_template, request, url_for, make_response, flash, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime
from sqlalchemy import func

#-----------imports for login--------------#
from flask_mail import Mail, Message
from authlib.integrations.flask_client import OAuth
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
import os
import base64 

app = Flask(__name__)

load_dotenv('a.env')

#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expense.db'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///local.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'FLASK_SECRET_KEY'
#---------Login app configs----------------#
app.config['MAIL_SERVER']   = 'smtp.gmail.com'
app.config['MAIL_PORT']     = 587
app.config['MAIL_USE_TLS']  = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME', '')

#app.config['GOOGLE_CLIENT_ID']     = os.environ.get('GOOGLE_CLIENT_ID', '')
#app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET', '')

app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')

db = SQLAlchemy(app)

mail = Mail(app)
oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

serialiser = URLSafeTimedSerializer(app.config['SECRET_KEY'])


class Expense(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  description = db.Column(db.String(120), nullable=False)
  amount = db.Column(db.Float, nullable=False)
  category = db.Column(db.String(50), nullable=False)
  date = db.Column(db.Date, nullable=False, default=date.today)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


#-------------Login Code---------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    #password = db.Column(db.String(100), nullable=False)
    password  = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    google_id = db.Column(db.String(128), unique=True, nullable=True)
    profile_pic = db.Column(db.Text, nullable=True) 
#---------------------------------------
class CustomCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
 

# This will create a database
with app.app_context(): 
    db.create_all()
    try:
        with db.engine.connect() as conn:
            conn.execute(db.text(
                'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS profile_pic TEXT'
            ))
            conn.commit()
    except Exception as e:
        print(f"Migration error: {e}")
        pass     

DEFAULT_CATEGORIES = [
    'Food & Dining',
    'Groceries',
    'Transport',
    'Rent',
    'Utilities',
    'Health & Medical',
    'Entertainment',
    'Shopping',
    'Personal Care',
    'Insurance',
    'Education',
    'Travel',
    'Savings & Investments',
    'Miscellaneous',
]
 
def get_user_categories(user_id):
    """Return default categories plus any custom ones added by the user."""
    custom = CustomCategory.query.filter_by(user_id=user_id).order_by(CustomCategory.name).all()
    custom_names = [c.name for c in custom]
    return DEFAULT_CATEGORIES + custom_names

#---------------------------------------------------------------------------------
def prase_date_or_none(s:str):
  if not s:
    return None
  try:
    return datetime.strptime(s, "%Y-%m-%d").date()
  
  except ValueError:
    return None

#-------------Login/Register/Logout Code---------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password and check_password_hash(user.password, password):
            session['loggedin'] = True
            session['id'] = user.id
            session['username'] = user.username
            return redirect(url_for('index'))
        else:
            flash('Incorrect username/password!', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Validate first
        error = validate_password(password)
        if error:
            flash(error, 'error')
            return render_template('register.html')

        # Then check if user exists
        exists = User.query.filter_by(username=username).first()
        if exists:
            flash('Account already exists!', 'error')
        else:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('You have successfully registered!', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')

def validate_password(password):
    if len(password) < 8:
        return 'Password must be at least 8 characters.'
    if not any(c.isupper() for c in password):
        return 'Password must contain at least one uppercase letter.'
    if not any(c.islower() for c in password):
        return 'Password must contain at least one lowercase letter.'
    if not any(c.isdigit() for c in password):
        return 'Password must contain at least one number.'
    if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
        return 'Password must contain at least one special character.'
    return None  



@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))


#------------ Google Login/Register/Logout/Reset Password -----------#
# Google login
@app.route('/login/google')
def google_login():
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/callback')
def google_callback():
    token     = google.authorize_access_token()
    user_info = token.get('userinfo')
    if not user_info:
        flash('Google login failed.', 'error')
        return redirect(url_for('login'))

    google_id = user_info['sub']
    email     = user_info.get('email', '')
    name      = user_info.get('name', email.split('@')[0])

    user = User.query.filter_by(google_id=google_id).first()
    if not user and email:
        user = User.query.filter_by(email=email).first()
        if user:
            user.google_id = google_id
            db.session.commit()
    if not user:
        base = name.replace(' ', '_').lower()
        username, counter = base, 1
        while User.query.filter_by(username=username).first():
            username = f"{base}{counter}"
            counter += 1
        user = User(username=username, email=email, google_id=google_id, password=None)
        db.session.add(user)
        db.session.commit()

    session['loggedin'] = True
    session['id']       = user.id
    session['username'] = user.username
    return redirect(url_for('index'))

# Forgot password
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email'].strip()
        user  = User.query.filter_by(email=email).first()
        if user:
            if user.password is None:
                flash('That account uses Google Sign-In. Please log in with Google.', 'error')
                return redirect(url_for('login'))
            token     = serialiser.dumps(email, salt='password-reset')
            reset_url = url_for('reset_password', token=token, _external=True)
            msg = Message('Reset your password', recipients=[email])
            msg.body = f'Click to reset your password: {reset_url}\n\nExpires in 1 hour.'
            mail.send(msg)
        flash('If that email is registered, a reset link has been sent.', 'success')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serialiser.loads(token, salt='password-reset', max_age=3600)
    except Exception:
        flash('Reset link is invalid or expired.', 'error')
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        new_password = request.form['password']
        user = User.query.filter_by(email=email).first()
        user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('Password updated! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', token=token)


#-------------------------Profile-----------------------------------

# Profile page
@app.route('/profile')
def profile():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    user = db.session.get(User, session['id'])
    if not user:
        return redirect(url_for('login'))
    is_google_user = user.google_id is not None and user.password is None
    return render_template('profile.html', user=user, is_google_user=is_google_user)


# Upload profile picture
@app.route('/profile/upload-pic', methods=['POST'])
def upload_pic():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    file = request.files.get('profile_pic')
    if file and file.filename:
        data = file.read()
        if len(data) > 2 * 1024 * 1024:  # 2MB limit
            flash('Image must be under 2MB.', 'error')
            return redirect(url_for('profile'))
        encoded = base64.b64encode(data).decode('utf-8')
        mime = file.content_type
        user = User.query.get(session['id'])
        user.profile_pic = f"data:{mime};base64,{encoded}"
        db.session.commit()
        flash('Profile picture updated!', 'success')
    return redirect(url_for('profile'))


# Change email
@app.route('/profile/change-email', methods=['POST'])
def change_email():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    new_email = request.form.get('email', '').strip()
    if not new_email:
        flash('Email cannot be empty.', 'error')
        return redirect(url_for('profile'))
    exists = User.query.filter_by(email=new_email).first()
    if exists and exists.id != session['id']:
        flash('That email is already in use.', 'error')
        return redirect(url_for('profile'))
    user = User.query.get(session['id'])
    user.email = new_email
    db.session.commit()
    flash('Email updated!', 'success')
    return redirect(url_for('profile'))


# Change password
@app.route('/profile/change-password', methods=['POST'])
def change_password():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    current = request.form.get('current_password', '')
    new_pw  = request.form.get('new_password', '')
    user = User.query.get(session['id'])
    if not check_password_hash(user.password, current):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('profile'))
    error = validate_password(new_pw)
    if error:
        flash(error, 'error')
        return redirect(url_for('profile'))
    user.password = generate_password_hash(new_pw)
    db.session.commit()
    flash('Password updated!', 'success')
    return redirect(url_for('profile'))

# Set password
@app.route('/profile/set-password', methods=['POST'])
def set_password():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    new_pw = request.form.get('new_password', '')
    error = validate_password(new_pw)
    if error:
        flash(error, 'error')
        return redirect(url_for('profile'))
    user = User.query.get(session['id'])
    user.password = generate_password_hash(new_pw)
    db.session.commit()
    flash('Password set! You can now log in with your username too.', 'success')
    return redirect(url_for('profile'))

# Delete account
@app.route('/profile/delete-account', methods=['POST'])
def delete_account():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['id'])
    Expense.query.filter_by(user_id=session['id']).delete()
    CustomCategory.query.filter_by(user_id=session['id']).delete()
    db.session.delete(user)
    db.session.commit()
    session.clear()
    flash('Your account has been deleted.', 'success')
    return redirect(url_for('login'))


#---------------------Custom Category---------------------------
 
@app.route('/categories/add', methods=['POST'])
def add_category():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    name = (request.form.get('category_name') or '').strip().title()
    if not name:
        flash('Category name cannot be empty.', 'error')
        return redirect(url_for('profile'))
    if name in DEFAULT_CATEGORIES:
        flash('That category already exists in the default list.', 'error')
        return redirect(url_for('profile'))
    exists = CustomCategory.query.filter_by(user_id=session['id'], name=name).first()
    if exists:
        flash('You already have that custom category.', 'error')
        return redirect(url_for('profile'))
    if len(name) > 50:
        flash('Category name must be 50 characters or fewer.', 'error')
        return redirect(url_for('profile'))
    new_cat = CustomCategory(user_id=session['id'], name=name)
    db.session.add(new_cat)
    db.session.commit()
    flash(f'Category "{name}" added!', 'success')
    return redirect(url_for('profile'))
 
 
@app.route('/categories/delete/<int:cat_id>', methods=['POST'])
def delete_category(cat_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    cat = CustomCategory.query.get_or_404(cat_id)
    if cat.user_id != session['id']:
        flash('Not authorised.', 'error')
        return redirect(url_for('profile'))
    db.session.delete(cat)
    db.session.commit()
    flash(f'Category "{cat.name}" removed.', 'success')
    return redirect(url_for('profile'))


#-----------------------------------------------------------------------

@app.route("/")
def index():

  if 'loggedin' not in session:
    return redirect(url_for('login'))
  
  categories = get_user_categories(session['id'])

  # all expenses for the user 
  all_expenses = Expense.query.filter_by(user_id=session['id']).all()

  # all time total for the user
  all_time_total = round(sum(e.amount for e in all_expenses),2)

  # montly average
  from collections import defaultdict
  monthly_totals = defaultdict(float)
  for e in all_expenses:
     monthly_totals[(e.date.year, e.date.month)] += e.amount
  monthly_avg = round(sum(monthly_totals.values()) / len(monthly_totals), 2) if monthly_totals else 0

  # top category for the spending
  category_tot = defaultdict(float)
  for e in all_expenses:
     category_tot[e.category] += e.amount
  top_category = max(category_tot, key=category_tot.get) if category_tot else "N/A"
  top_category_amount = round(category_tot[top_category], 2) if category_tot else 0   


  # Reading the query strings and grouping them
  start_str = (request.args.get("start") or "").strip()
  end_str = (request.args.get("end") or "").strip()

  # selected category from query string
  selected_category = (request.args.get("category") or "").strip()


  # Prasing the date strings
  start_date = prase_date_or_none(start_str)
  end_date = prase_date_or_none(end_str)

  if start_date and end_date and end_date < start_date:
    flash("End date cannot be earlier than start date", "error")
    # restarting the start and end date to None
    start_date = end_date = None
    start_str = end_str = ""

  q = Expense.query.filter_by(user_id=session['id'])
  #q = Expense.query
  if start_date:
    q = q.filter(Expense.date >= start_date)
  if end_date:
    q = q.filter(Expense.date <= end_date)

  if selected_category:
    q = q.filter(Expense.category == selected_category)

  expenses = q.order_by(Expense.date.desc(), Expense.id.desc()).all()
  total = round(sum(e.amount for e in expenses), 2)


  cat_q = db.session.query(Expense.category, func.sum(Expense.amount))

  if start_date:
    cat_q = cat_q.filter(Expense.date >= start_date)
  if end_date:
    cat_q = cat_q.filter(Expense.date <= end_date)
  
  if selected_category:
    cat_q = cat_q.filter(Expense.category == selected_category)

  cat_row = cat_q.group_by(Expense.category).all()
  cat_labels = [c for c, _ in cat_row]
  cat_amounts = [round(float(s or 0), 3) for _, s in cat_row]

  user = User.query.get(session['id'])

  return render_template(
    
    "index.html", 
  
    categories=categories,
    today=date.today().isoformat(),
    expenses=expenses,
    total=total,
    start_str=start_str,
    end_str=end_str,
    selected_category=selected_category,
    cat_labels=cat_labels,
    cat_amounts=cat_amounts,
    all_time_total=all_time_total,       
    monthly_avg=monthly_avg,             
    top_category=top_category,         
    top_category_amount=top_category_amount,  
    current_user_pic = user.profile_pic

    )
#----------------------------------Adding Category-----------------------------------------

@app.route("/add", methods=['POST'])
def add():
  if 'loggedin' not in session:
    return redirect(url_for('login'))
 
  description = (request.form.get("description") or "").strip()
  amount_str = (request.form.get("amount") or "").strip()
  date_str = (request.form.get("date") or "").strip()
 
  # Handle custom category
  category = (request.form.get("category") or "").strip()
  custom_category = (request.form.get("custom_category") or "").strip().title()
  if category == "__custom__":
    if not custom_category:
      flash("Please enter a custom category name.", "error")
      return redirect(url_for("index"))
    if len(custom_category) > 50:
      flash("Category name must be 50 characters or fewer.", "error")
      return redirect(url_for("index"))
    # Save it so it appears next time
    all_cats = get_user_categories(session['id'])
    if custom_category not in all_cats:
      new_cat = CustomCategory(user_id=session['id'], name=custom_category)
      db.session.add(new_cat)
      db.session.commit()
    category = custom_category
 
  if not description or not amount_str or not category:
    flash("Please fill description, amount, and category", "error")
    return redirect(url_for("index"))
 
  try:
    amount = float(amount_str)
    if amount <= 0:
      raise ValueError
  except ValueError:
    flash("Amount must be a positive number", "error")
    return redirect(url_for("index"))
 
  try:
    d = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else date.today()
  except ValueError:
    d = date.today()
 
  e = Expense(description=description, amount=amount, category=category, date=d,
              user_id=session['id'])
  db.session.add(e)
  db.session.commit()
 
  flash("Expense added", "success")
  return redirect(url_for("index"))
 
#------------------------------Delete Expense------------------------------
 
@app.route('/delete/<int:expense_id>', methods=['POST'])
def delete(expense_id):
  e = Expense.query.get_or_404(expense_id)
  db.session.delete(e)
  db.session.commit()
  flash("Expense deleted", "success")
  return redirect(url_for("index"))
 
#-----------------------------Analytics----------------------------------------
@app.route("/analytics")
def analytics():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
 
    cat_row = db.session.query(
        Expense.category, 
        func.sum(Expense.amount)
    ).filter(Expense.user_id == session['id']).group_by(Expense.category).all()
    
    cat_labels = [c for c, _ in cat_row]
    cat_amounts = [round(float(s or 0), 2) for _, s in cat_row]
 
    day_row = db.session.query(
        Expense.date, 
        func.sum(Expense.amount)
    ).filter(Expense.user_id == session['id']).group_by(Expense.date).order_by(Expense.date).all()
 
    dates = [d.strftime("%Y-%m-%d") for d, _ in day_row]
    daily_totals = [round(float(s or 0), 2) for _, s in day_row]
 
    user = User.query.get(session['id'])
 
    return render_template(
        "analytics.html",
        categories=cat_labels,
        category_totals=cat_amounts,
        dates=dates,
        daily_totals=daily_totals,
        current_user_pic=user.profile_pic
    )

if __name__ == "__main__":
  #app.run(debug=True, port=2030)
  app.run(debug=True, host='127.0.0.1', port=2030)
