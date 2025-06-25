from flask import Flask, render_template, request, redirect, session, url_for
from flask_session import Session
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector

# App setup
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL DB config
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Pratham@123",
    database="biharyatrasetu"
)

# Session config
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Mail config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'quizhunt413@gmail.com'
app.config['MAIL_PASSWORD'] = 'isdr hbaa gcti vafo'
mail = Mail(app)

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/destinations')
def destinations():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM destinations")
    destinations = cursor.fetchall()
    cursor.close()
    return render_template('destinations.html', destinations=destinations)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        cursor = db.cursor()
        sql = "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)"
        cursor.execute(sql, (name, email, password))
        db.commit()
        cursor.close()
        return redirect('/login')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password_input = request.form['password']

        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()

        if user and check_password_hash(user['password'], password_input):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            return redirect('/')
        else:
            return "Invalid credentials"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM destinations")
    destinations = cursor.fetchall()

    if request.method == 'POST':
        if 'user_id' not in session:
            return redirect('/login')

        destination_id = request.form['destination']
        date = request.form['date']
        travelers = int(request.form['travelers'])
        user_id = session['user_id']

        amount = travelers * 599  # ₹599 per traveler

        sql = "INSERT INTO bookings (destination_id, booking_date, travelers, amount, user_id, payment_status) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(sql, (destination_id, date, travelers, amount, user_id, 'Pending'))
        db.commit()

        booking_id = cursor.lastrowid  # get newly created booking id

        # Confirmation Email
        msg = Message('Bihar Yatra Setu | Booking Confirmed!',
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[session['user_email']])
        msg.body = f"Hello {session['user_name']},\n\nYour booking for destination ID {destination_id} on {date} for {travelers} traveler(s) has been confirmed.\n\nTotal Amount: ₹{amount}\n\nThank you for choosing Bihar Yatra Setu!"
        mail.send(msg)

        cursor.close()
        return redirect(f'/payment/{booking_id}')

    cursor.close()
    return render_template('booking.html', destinations=destinations)

@app.route('/payment/<int:booking_id>')
def payment(booking_id):
    if 'user_id' not in session:
        return redirect('/login')

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT b.id, d.name AS destination, b.booking_date, b.travelers, b.payment_status
        FROM bookings b
        JOIN destinations d ON b.destination_id = d.id
        WHERE b.id = %s AND b.user_id = %s
    """, (booking_id, session['user_id']))
    booking = cursor.fetchone()

    if not booking:
        cursor.close()
        return redirect('/my-bookings')

    booking_amount = int(booking['travelers']) * 599

    cursor.close()
    return render_template('payment.html', booking=booking, booking_amount=booking_amount)

@app.route('/confirm-payment/<int:booking_id>', methods=['POST'])
def confirm_payment(booking_id):
    if 'user_id' not in session:
        return redirect('/login')

    cursor = db.cursor()
    cursor.execute("""
        UPDATE bookings SET payment_status = 'Paid'
        WHERE id = %s AND user_id = %s
    """, (booking_id, session['user_id']))
    db.commit()
    cursor.close()

    return redirect('/my-bookings')



@app.route('/my-bookings')
def my_bookings():
    if 'user_id' not in session:
        return redirect('/login')

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.id, d.name AS destination, b.booking_date, b.travelers, b.amount, b.payment_status
        FROM bookings b
        JOIN destinations d ON b.destination_id = d.id
        WHERE b.user_id = %s
        ORDER BY b.id DESC
    """, (session['user_id'],))
    bookings = cursor.fetchall()
    cursor.close()

    return render_template('my_bookings.html', bookings=bookings)


@app.route('/cancel-booking/<int:booking_id>')
def cancel_booking(booking_id):
    if 'user_id' not in session:
        return redirect('/login')

    cursor = db.cursor(dictionary=True)

    # Fetch booking details before deleting
    cursor.execute("""
        SELECT b.id, d.name AS destination, b.booking_date, b.travelers
        FROM bookings b
        JOIN destinations d ON b.destination_id = d.id
        WHERE b.id = %s AND b.user_id = %s
    """, (booking_id, session['user_id']))
    booking = cursor.fetchone()

    if not booking:
        cursor.close()
        return redirect('/my-bookings')  # Invalid booking id or unauthorized

    # Send cancellation email
    msg = Message('Bihar Yatra Setu | Booking Cancelled',
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[session['user_email']])
    msg.body = f"""Hello {session['user_name']},

Your booking for {booking['destination']} on {booking['booking_date']} for {booking['travelers']} traveler(s) has been successfully cancelled.

We're sorry to see you cancel — hope to serve you again soon!

Thank you,
Team Bihar Yatra Setu
"""
    mail.send(msg)

    # Delete the booking
    cursor.execute("DELETE FROM bookings WHERE id = %s AND user_id = %s", (booking_id, session['user_id']))
    db.commit()
    cursor.close()

    return redirect('/my-bookings')


@app.route('/reviews', methods=['GET', 'POST'])
def reviews():
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        if 'user_id' not in session:
            return redirect('/login')

        destination_id = request.form['destination']
        review_text = request.form['review']
        date = request.form['date']

        sql = "INSERT INTO reviews (name, destination_id, review, date_posted) VALUES (%s, %s, %s, %s)"
        values = (session['user_name'], destination_id, review_text, date)
        cursor.execute(sql, values)
        db.commit()

        return redirect('/reviews')

    cursor.execute("SELECT * FROM destinations")
    destinations = cursor.fetchall()

    cursor.execute("""
        SELECT r.id, r.name, r.review, d.name AS destination, r.date_posted 
        FROM reviews r 
        JOIN destinations d ON r.destination_id = d.id
        ORDER BY r.id DESC
    """)
    reviews = cursor.fetchall()
    cursor.close()

    return render_template('reviews.html', destinations=destinations, reviews=reviews)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        cursor = db.cursor()
        sql = "INSERT INTO contact (name, email, message) VALUES (%s, %s, %s)"
        cursor.execute(sql, (name, email, message))
        db.commit()
        cursor.close()

        return redirect('/contact?success=1')

    return render_template('contact.html')

# Run app
if __name__ == '__main__':
    app.run(debug=True)
