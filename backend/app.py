from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import uuid
import re
import os
import subprocess
import json
from flask_mail import Mail, Message
from flask_apscheduler import APScheduler
import speech_recognition as sr
from gtts import gTTS
import io

app = Flask(__name__)
CORS(app)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

mail = Mail(app)


class Config:
    SCHEDULER_API_ENABLED = True


app.config.from_object(Config())
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

users = {}

knowledge_base = {}


def load_knowledge_base():
    global knowledge_base
    try:
        with open('backend/medicationkb.json', 'r') as f:
            knowledge_base = json.load(f).get("medications", {})
            print("Medication knowledge base loaded successfully.")
    except (FileNotFoundError, json.JSONDecodeError):
        print("ERROR: medicationkb.json not found or is invalid.")
        knowledge_base = {}


# Load the KB once at startup for efficiency
load_knowledge_base()


def parse_time(reminder_time: str):
    """Convert 'HH:MM AM/PM' or 'HH:MM' (24h) into hour/minute."""
    match = re.match(r"(\d{1,2}):(\d{2})\s?(AM|PM)?", reminder_time, re.I)
    if not match:
        raise ValueError("Invalid time format. Use HH:MM or HH:MM AM/PM")
    hour = int(match.group(1))
    minute = int(match.group(2))
    meridian = match.group(3)

    if meridian:
        meridian = meridian.upper()
        if meridian == "PM" and hour < 12:
            hour += 12
        if meridian == "AM" and hour == 12:
            hour = 0

    return hour, minute


def send_single_reminder(med):
    """Send email reminder for a medicine to the user who added it."""
    with app.app_context():
        email = med.get('email')
        try:
            msg = Message(
                subject=f"Reminder: Take {med['name']}", recipients=[email])
            msg.body = f"It's time to take your medicine: {med['name']} ({med['dose']}) at {med['reminderTime']}"
            mail.send(msg)
            print(f"Reminder sent for {med['name']} to {email}")
        except Exception as e:
            print(f"Failed to send reminder for {med['name']}: {e}")


def schedule_reminder(med):
    """Schedule a daily reminder for a medicine."""
    job_id = f"reminder_{med['id']}"

    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    try:
        hour, minute = parse_time(med['reminderTime'])
        scheduler.add_job(id=job_id, func=lambda m=med: send_single_reminder(
            m), trigger='cron', hour=hour, minute=minute)
        print(f"Scheduled reminder for {med['name']} at {med['reminderTime']}")
    except Exception as e:
        print(f"Failed to schedule reminder for: {e}")

# --- API Endpoints ---

# --- NEW: Intelligent Details Endpoint ---


@app.route('/medicines/details/<string:med_name>', methods=['GET'])
def get_medicine_details(med_name):
    search_name_lower = med_name.lower()
    if not knowledge_base:
        return jsonify({'error': 'Knowledge base is not loaded'}), 500

    # First, check if the search name is a direct generic name (a key)
    if search_name_lower in knowledge_base:
        return jsonify(knowledge_base[search_name_lower]), 200

    # If not, loop through all medicines to check brand names
    for med_key, med_data in knowledge_base.items():
        brand_names_lower = [name.lower()
                             for name in med_data.get('brand_names', [])]
        if search_name_lower in brand_names_lower:
            # Found it! Return the parent object's data
            return jsonify(med_data), 200

    # If we get here, the medicine was not found
    return jsonify({'error': 'Medicine not found in knowledge base'}), 404


@app.route('/check-interactions', methods=['POST'])
def check_interactions():
    data = request.get_json()
    medication_names = data.get('medicines', [])

    if not medication_names or len(medication_names) < 2:
        return jsonify({'warnings': []}), 200

    warnings = set()
    med_names_lower = [name.lower() for name in medication_names]

    for i in range(len(med_names_lower)):
        for j in range(i + 1, len(med_names_lower)):
            med1_name = med_names_lower[i]
            med2_name = med_names_lower[j]

            med1_data = knowledge_base.get(med1_name)
            if med1_data:
                for group in med1_data.get('interactions', []):
                    if group.get('type') == 'other_drugs':
                        for interaction in group.get('interactions_list', []):
                            if med2_name in interaction.get('interactant', '').lower():
                                detail = interaction.get(
                                    'details', 'Interaction details not provided.')
                                warnings.add(
                                    f"Warning: {med1_name.capitalize()} and {med2_name.capitalize()}. {detail}")

            med2_data = knowledge_base.get(med2_name)
            if med2_data:
                for group in med2_data.get('interactions', []):
                    if group.get('type') == 'other_drugs':
                        for interaction in group.get('interactions_list', []):
                            if med1_name in interaction.get('interactant', '').lower():
                                detail = interaction.get(
                                    'details', 'Interaction details not provided.')
                                warnings.add(
                                    f"Warning: {med2_name.capitalize()} and {med1_name.capitalize()}. {detail}")

    return jsonify({'warnings': sorted(list(warnings))}), 200


@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name or not email or not password:
        return jsonify({'message': 'Name, Email and password required'}), 400
    if email in users:
        return jsonify({'message': 'User already exists'}), 409

    users[email] = {"password": password, "name": name, "medicines": []}
    return jsonify({'message': f'Signed up successfully as {name}!'}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email and password required'}), 400
    user_data = users.get(email)
    if not user_data or user_data["password"] != password:
        return jsonify({'message': 'Incorrect email or password'}), 401

    return jsonify({'message': f'Welcome {user_data.get("name", email)}!', 'email': email, 'name': user_data.get("name")}), 200


@app.route('/medicines', methods=['GET'])
def get_medicines():
    email = request.args.get('email')
    if not email or email not in users:
        return jsonify({'medicines': []}), 200
    return jsonify({'medicines': users[email]["medicines"]}), 200


@app.route('/medicines', methods=['POST'])
def add_medicine():
    data = request.get_json()
    email = data.get('email')
    name = data.get('name')
    dose = data.get('dose')
    reminder_time = data.get('reminderTime')

    if not email or email not in users:
        return jsonify({'message': 'Invalid or missing user'}), 401
    if not name or not dose or not reminder_time:
        return jsonify({'message': 'Name, dose, and reminder time are required'}), 400

    medicine = {
        'id': str(uuid.uuid4()),
        'name': name,
        'dose': dose,
        'reminderEnabled': True,
        'reminderTime': reminder_time,
        'email': email
    }

    users[email]["medicines"].append(medicine)
    schedule_reminder(medicine)

    return jsonify({'message': f'Medicine {name} added successfully', 'medicine': medicine}), 201


@app.route('/medicines/<string:medicine_id>', methods=['PUT'])
def update_medicine(medicine_id):
    data = request.get_json()
    email = data.get('email')
    name = data.get('name')
    dose = data.get('dose')
    reminder_time = data.get('reminderTime')

    if not email or email not in users:
        return jsonify({'message': 'Invalid or missing user'}), 401
    if not name or not dose or not reminder_time:
        return jsonify({'message': 'Name, dose, and reminder time are required'}), 400

    for med in users[email]["medicines"]:
        if med['id'] == medicine_id:
            med['name'] = name
            med['dose'] = dose
            med['reminderTime'] = reminder_time
            schedule_reminder(med)
            return jsonify({'message': 'Medicine updated successfully', 'medicine': med}), 200

    return jsonify({'message': 'Medicine not found'}), 404


@app.route('/medicines/<string:medicine_id>', methods=['DELETE'])
def delete_medicine(medicine_id):
    email = request.args.get('email')
    if not email or email not in users:
        return jsonify({'message': 'Invalid or missing user'}), 401

    job_id = f"reminder_{medicine_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    initial_len = len(users[email]["medicines"])
    users[email]["medicines"] = [m for m in users[email]
                                 ["medicines"] if m['id'] != medicine_id]
    if len(users[email]["medicines"]) == initial_len:
        return jsonify({'message': 'Medicine not found'}), 404
    return jsonify({'message': 'Medicine deleted'}), 200


@app.route("/transcribe", methods=["POST"])
def transcribe_audio():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    uid = str(uuid.uuid4())
    wav_path = f"{uid}.wav"

    try:
        uploaded_file.save(f"{uid}.input")
        subprocess.run(
            ["ffmpeg", "-y", "-i", f"{uid}.input", "-ar", "16000", "-ac", "1", wav_path], check=True)

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)

        text = recognizer.recognize_google(audio_data)

    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"ffmpeg conversion failed: {e}"}), 500
    except sr.UnknownValueError:
        text = "Could not understand audio."
    except sr.RequestError as e:
        text = f"Could not request results; {e}"
    except Exception as e:
        text = f"Unexpected error: {e}"
    finally:
        for f in [f"{uid}.input", wav_path]:
            if os.path.exists(f):
                os.remove(f)

    return jsonify({"transcription": text})


@app.route('/speak', methods=['GET'])
def speak():
    text_to_speak = request.args.get('text')

    if not text_to_speak:
        return jsonify({'error': 'No text provided'}), 400

    try:
        tts = gTTS(text=text_to_speak, lang='en', slow=False)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)

        return send_file(mp3_fp, mimetype='audio/mpeg')

    except Exception as e:
        return jsonify({'error': f'Failed to generate speech: {e}'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
