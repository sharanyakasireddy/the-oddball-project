from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import requests

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

# Booking model
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(150), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    sex = db.Column(db.String(10), nullable=False)
    blood_group = db.Column(db.String(10), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hospital = db.relationship('User', backref=db.backref('appointments', lazy=True))

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

# Login page
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

# Signup page
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
            correct_passkey = "hospitalpasskey"  # The passkey required for hospitals
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

    # Get all bookings for this hospital
    bookings = Booking.query.filter_by(hospital_id=current_user.id).all()
    
    return render_template('hospital_interface.html', bookings=bookings)

# Customer Interface
@app.route('/customer')
@login_required
def customer_interface():
    if current_user.role != 'customer':
        return redirect(url_for('login'))
    return render_template('customer_interface.html')

# Toolbar Option Routes
@app.route('/hospital_availability')
@login_required
def hospital_availability():
    return render_template('hospital_availability.html')

@app.route('/emergency_contact')
@login_required
def emergency_contact():
    return render_template('emergency_contact.html')

@app.route('/navigation_directions')
@login_required
def navigation_directions():
    return render_template('navigation_directions.html')

@app.route('/queue_status')
@login_required
def queue_status():
    return render_template('queue_status.html')

# Bookings & Pre-Registration
@app.route('/booking_pre_registration')
@login_required
def booking_pre_registration():
    if current_user.role != 'customer':
        return redirect(url_for('login'))
    
    # Query all hospitals from the database
    hospitals = User.query.filter_by(role='hospital').all()
    
    # Pass the list of hospitals to the template
    return render_template('booking_pre_registration.html', hospitals=hospitals)

# Handle the hospital booking
@app.route('/hospital_booking/<int:hospital_id>', methods=['POST'])
@login_required
def hospital_booking(hospital_id):
    # Retrieve the hospital information using hospital_id
    hospital = User.query.get_or_404(hospital_id)
    
    # Render a template or handle the booking logic here
    return render_template('hospital_booking.html', hospital=hospital)

# Confirm booking
@app.route('/confirm_booking/<int:hospital_id>', methods=['POST'])
@login_required
def confirm_booking(hospital_id):
    # Get the form data
    patient_name = request.form.get('patient_name')
    age = request.form.get('age')
    sex = request.form.get('sex')
    blood_group = request.form.get('blood_group')
    
    # Create a new booking record
    new_booking = Booking(
        patient_name=patient_name,
        age=age,
        sex=sex,
        blood_group=blood_group,
        hospital_id=hospital_id
    )
    db.session.add(new_booking)
    db.session.commit()

    flash(f'Booking confirmed for {patient_name} at {User.query.get(hospital_id).username}!')
    return redirect(url_for('hospital_interface'))

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

@app.route('/beds_opd_availability')
@login_required
def beds_opd_availability():
    # Render the Beds & OPD Availability page
    return render_template('beds_opd_availability.html')

# Appointment Requests
@app.route('/appointment_requests')
@login_required
def appointment_requests():
    # Render the Appointment Requests page
    return render_template('appointment_requests.html')

# Incoming Emergency Patients
@app.route('/incoming_emergency_patients')
@login_required
def incoming_emergency_patients():
    # Render the Incoming Emergency Patients page
    return render_template('incoming_emergency_patients.html')

# Search for a Place
@app.route('/search_place', methods=['GET', 'POST'])
@login_required
def search_place():
    if request.method == 'POST':
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        
        # URL for the Google Places API Nearby Search
        url = "https://google-maps-api-free.p.rapidapi.com/google-places-nearby-search"
        querystring = {
            "location": f"{latitude},{longitude}",
            "radius": "5000",  # Search within a 5km radius
            "type": "hospital"
        }

        headers = {
            "x-rapidapi-key": "9dfefe5774msh77168a4e8db1317p1396e5jsn118ab7f95baa",
            "x-rapidapi-host": "google-maps-api-free.p.rapidapi.com"
        }

        try:
            response = requests.get(url, headers=headers, params=querystring)
            response.raise_for_status()
            data = response.json()
            if 'results' in data:
                results = data['results']
                return render_template('search_place.html', results=results)
            else:
                flash('No results found.')

        except requests.exceptions.HTTPError as http_err:
            flash(f'HTTP error occurred: {http_err}')
        except Exception as err:
            flash(f'Other error occurred: {err}')

    return render_template('search_place.html')

if __name__ == '__main__':
    add_test_hospitals()  # Add the test hospitals when the app starts
    app.run(debug=True)

