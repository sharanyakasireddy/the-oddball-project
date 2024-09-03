from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'customer' or 'hospital'

# Create DB if it doesn't exist
with app.app_context():
    db.create_all()

# Load user for LoginManager
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home page route that redirects to the login page
@app.route('/')
def home():
    return redirect(url_for('login'))

# Home/Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            if user.role == 'customer':
                return redirect(url_for('customer_interface'))
            elif user.role == 'hospital':
                return redirect(url_for('hospital_interface'))
        else:
            flash('Login failed. Check your username and password.')
    return render_template('login.html')

# Signup page (for customers and hospitals)
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        passkey = request.form.get('passkey')

        # Check if user already exists
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists. Please log in.')
            return redirect(url_for('login'))

        if role == 'hospital':
            correct_passkey = "ENV.PASSKEY"  # The passkey required for hospitals
            if passkey != correct_passkey:
                flash('Invalid passkey for hospital registration.')
                return redirect(url_for('signup'))

        # Create a new user with the appropriate role
        new_user = User(username=username, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('Signup successful! Please log in.')
        return redirect(url_for('login'))

    return render_template('signup.html')

# Hospital Interface
@app.route('/hospital')
@login_required
def hospital_interface():
    if current_user.role != 'hospital':
        return redirect(url_for('login'))
    return render_template('hospital_interface.html')

# Customer Interface
@app.route('/customer')
@login_required
def customer_interface():
    if current_user.role != 'customer':
        return redirect(url_for('login'))
    return render_template('customer_interface.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Add test hospitals within the application context
def add_test_hospitals():
    with app.app_context():
        # Check if hospitals already exist, and if not, add them
        if not User.query.filter_by(username="hospital1").first():
            hospital1 = User(username="hospital1", password="hospitalpass1", role="hospital")
            db.session.add(hospital1)

        if not User.query.filter_by(username="hospital2").first():
            hospital2 = User(username="hospital2", password="hospitalpass2", role="hospital")
            db.session.add(hospital2)

        if not User.query.filter_by(username="hospital3").first():
            hospital3 = User(username="hospital3", password="hospitalpass3", role="hospital")
            db.session.add(hospital3)

        db.session.commit()

if __name__ == '__main__':
    add_test_hospitals()  # Add the test hospitals when the app starts
    app.run(debug=True)




