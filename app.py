from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_cors import CORS
import pymysql
import json

app = Flask(__name__)
CORS(app)
app.secret_key = 'your_secret_key'

# MySQL RDS configuration
db_config = {
    'host': 'stressdb.ch2mqkeiggw8.us-west-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'sqlBhai1234567',
    'database': 'stressdb'
}


# Homepage
@app.route('/')
def landpage():
    return render_template('landpage.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if email == 'admin@gmail.com' and password == 'admin123':
            session['loggedin'] = True
            session['id'] = 'admin'
            session['email'] = email
            return redirect(url_for('home'))

        try:
            connection = pymysql.connect(**db_config)
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
            user = cursor.fetchone()
            cursor.close()
            connection.close()

            if user:
                session['loggedin'] = True
                session['id'] = user[0]
                session['email'] = user[2]
                return redirect(url_for('home'))
            else:
                return render_template('login.html', error='Invalid credentials')

        except Exception as e:
            return render_template('login.html', error=str(e))

    return render_template('login.html')

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        gender = request.form['gender']
        age = request.form['age']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')

        try:
            connection = pymysql.connect(**db_config)
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO users (name, email, password, gender, age)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, email, password, gender, age))
            connection.commit()
            cursor.close()
            connection.close()
            return redirect(url_for('login'))

        except Exception as e:
            return render_template('register.html', error=str(e))

    return render_template('register.html')

# Home
@app.route('/home')
def home():
    if 'loggedin' in session:
        return render_template('home.html', username=session['email'])
    return redirect(url_for('login'))

# Feedback Page
@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

# Feedback Submission
@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        feedback_text = request.form.get('feedback')
        rating = request.form.get('rating')

        if not name or not email or not feedback_text or not rating:
            return jsonify({"error": "All fields are required"}), 400

        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                return jsonify({"error": "Rating must be between 1 and 5"}), 400
        except ValueError:
            return jsonify({"error": "Invalid rating format"}), 400

        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO feedback (name, email, feedback_text, rating)
            VALUES (%s, %s, %s, %s)
        """, (name, email, feedback_text, rating))
        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({"message": "Feedback submitted successfully", "name": name, "rating": rating})

    except Exception as e:
        return jsonify({"error": "An error occurred", "details": str(e)}), 500

# Feedback data for chart
@app.route('/feedback-data')
def feedback_data():
    try:
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute("SELECT rating, COUNT(*) FROM feedback GROUP BY rating ORDER BY rating")
        ratings = cursor.fetchall()
        cursor.close()
        connection.close()

        rating_counts = {str(row[0]): row[1] for row in ratings}
        return jsonify(rating_counts)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Load chatbot intents
with open('intents.json', 'r') as file:
    intents = json.load(file)

def get_chatbot_response(user_message):
    for intent in intents['intents']:
        if user_message.lower() in map(str.lower, intent['patterns']):
            return intent['responses'][0]
    return "Sorry, I didn't understand that. Could you rephrase?"

# Chat route
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message')
    if not user_message:
        return jsonify({"response": "Message is empty. Please type something."})

    bot_response = get_chatbot_response(user_message)
    return jsonify({"response": bot_response})

# Static pages
@app.route('/psychiatrist')
def psychiatrist():
    return render_template('pysc.html')

@app.route('/yournotalone')
def yournotalone():
    return render_template('youarenotalone.html')

@app.route('/community')
def community():
    return render_template('community.html')

@app.route('/motivation')
def motivation():
    return render_template('motivational.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
