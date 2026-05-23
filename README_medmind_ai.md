# 💊 MedMind AI — Intelligent Voice Medication Assistant

A privacy-focused, voice-activated medication management system that helps elderly users manage their medications safely — featuring **Speech-to-Text**, **Text-to-Speech**, a curated **36-drug knowledge base**, and an intelligent **drug interaction checker**.

> Developed as part of the Capstone Project-1, MS in Artificial Intelligence & Machine Learning — Drexel University (2025).

---

## 🎯 Problem Statement

Medication non-adherence and adverse drug interactions are critical public health challenges, particularly for the elderly. Existing solutions often lack the accessibility required for users who may be less tech-savvy or have visual impairments.

MedMind AI addresses this by combining:
- **Voice interface** — lowering the barrier to entry for elderly users
- **Curated medication knowledge base** — providing accurate, verified drug information
- **Intelligent interaction checking** — proactively warning users about dangerous drug combinations
- **Privacy-first architecture** — designed for local execution without sensitive data leaving the device

---

## 🏗️ System Architecture

```
User / Caregiver
      │
      ▼
┌─────────────────────────────────────────────┐
│           Voice Interface Layer             │
│                                             │
│  ┌──────────────┐    ┌──────────────────┐  │
│  │ Speech-to-   │    │  Text-to-Speech  │  │
│  │ Text (STT)   │    │  (TTS) — gTTS    │  │
│  │ SpeechRecog  │    │  Audio Streaming │  │
│  │ + ffmpeg     │    │  via Flask API   │  │
│  └──────┬───────┘    └──────────────────┘  │
└─────────┼───────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────┐
│            Flask REST API Backend           │
│                                             │
│  /transcribe  → STT processing             │
│  /speak       → TTS audio generation       │
│  /medicines   → CRUD operations            │
│  /medicines/details → KB lookup            │
│  /check-interactions → Drug safety check   │
│  /signup, /login → User auth               │
└─────────┬───────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────┐
│       Medication Knowledge Base             │
│       (medicationkb.json)                   │
│                                             │
│  36 curated drugs                          │
│  Generic + brand name lookup              │
│  Dosage, uses, interactions               │
│  Food, alcohol, drug-drug interactions    │
│                                             │
│  Sources: FDA OpenFDA · Mayo Clinic        │
│           Drugs.com · MedlinePlus          │
└─────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────┐
│         Reminder & Notification System      │
│                                             │
│  APScheduler → Daily cron reminders        │
│  Flask-Mail  → Email notifications         │
│  React Native Frontend (by collaborator)   │
└─────────────────────────────────────────────┘
```

---

## ✨ Key Features

### 🎤 Voice Interface
- **Speech-to-Text** — accepts audio input, converts via ffmpeg pipeline, transcribes using Google SpeechRecognition API
- **Text-to-Speech** — generates natural audio responses using gTTS, streams MP3 directly to the user

### 💊 Medication Knowledge Base
- **36 curated medications** commonly prescribed to elderly patients
- Manually curated from FDA OpenFDA, Mayo Clinic, Drugs.com, and MedlinePlus
- Supports lookup by **both generic and brand names**
- Contains dosage guidelines, intended uses, and comprehensive interaction data

### ⚠️ Drug Interaction Checker
- Accepts a list of medications and cross-checks all combinations
- Detects **drug-drug interactions** from the knowledge base
- Returns specific interaction warnings with clinical detail
- Supports checking food and alcohol interactions per medication

### 💌 Smart Reminder System
- Daily medication reminders via **email notifications**
- Cron-based scheduling using APScheduler
- Supports custom reminder times per medication
- Integrated with React Native frontend for on-screen alerts

### 🔐 Privacy-First Design
- Local execution architecture — no sensitive medical data sent to third parties
- Knowledge base curated from public sources — no licensed database dependency
- Environment-variable based credential management

---

## 📊 Project Outcomes

| Feature | Implementation | Status |
|---------|---------------|--------|
| Speech-to-Text | SpeechRecognition + ffmpeg + Google API | ✅ Complete |
| Text-to-Speech | gTTS audio streaming | ✅ Complete |
| Medication KB | 36 drugs, JSON knowledge base | ✅ Complete |
| Brand name lookup | Generic + brand name search | ✅ Complete |
| Interaction checker | Multi-drug cross-check | ✅ Complete |
| Email reminders | APScheduler + Flask-Mail | ✅ Complete |
| User authentication | Signup/Login endpoints | ✅ Complete |
| Mobile frontend | React Native (collaborator) | ✅ Complete |

---

## 🔬 Technical Deep Dive

### Speech-to-Text Pipeline
```
Audio Input (any format)
        │
        ▼
ffmpeg conversion → 16kHz mono WAV
        │
        ▼
SpeechRecognition → Google Speech API
        │
        ▼
Transcribed text returned as JSON
```

### Knowledge Base Structure
```json
{
  "medications": {
    "generic_name": {
      "brand_names": ["BrandA", "BrandB"],
      "uses": "...",
      "dosage": "...",
      "interactions": [
        {
          "type": "other_drugs",
          "interactions_list": [
            {
              "interactant": "drug_name",
              "details": "clinical detail"
            }
          ]
        },
        {
          "type": "food",
          "interactions_list": [...]
        },
        {
          "type": "alcohol",
          "interactions_list": [...]
        }
      ]
    }
  }
}
```

### Interaction Checker Logic
```python
# Cross-checks all medication pairs
for each pair (med1, med2) in medications:
    check med1's interactions for med2
    check med2's interactions for med1
    collect and deduplicate warnings
return sorted list of clinical warnings
```

---

## 📁 Repository Structure

```
medmind-ai-voice-assistant/
│
├── README.md                    
├── requirements.txt             
├── .gitignore                   
├── .env.example                 ← Credential template
│
├── backend/
│   ├── app.py                   ← Flask API + STT/TTS + Core Logic
│   └── medicationkb.json        ← Curated 36-drug knowledge base
│   
│
├── docs/
│   └── project_report.pdf       ← Final project report
│
└── CONTRIBUTORS.md              ← Clear contribution split
```
---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.9+
- ffmpeg installed on your system
- Gmail account with App Password enabled (for email reminders)

### Install ffmpeg

**Windows:**
```bash
winget install ffmpeg
```

**Mac:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

### Installation

```bash
# Clone the repository
git clone https://github.com/Yati10-ss/medmind-ai-voice-assistant.git
cd medmind-ai-voice-assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your credentials
MAIL_USERNAME=your_gmail@gmail.com
MAIL_PASSWORD=your_gmail_app_password
```

> 💡 **Getting a Gmail App Password:** Go to myaccount.google.com → Security → 2-Step Verification → App Passwords → Generate

### Running the Backend

```bash
# Make sure medicationkb.json is in backend/ folder
cd backend
python app.py

# Server starts at http://localhost:3000
```

---

## 🔌 API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/transcribe` | POST | Upload audio file → get transcribed text |
| `/speak` | GET | `?text=...` → returns MP3 audio stream |
| `/medicines/details/<name>` | GET | Get full drug info by generic or brand name |
| `/check-interactions` | POST | Check interactions for a list of medications |
| `/medicines` | GET | Get all medications for a user |
| `/medicines` | POST | Add a new medication with reminder |
| `/medicines/<id>` | PUT | Update a medication |
| `/medicines/<id>` | DELETE | Remove a medication |
| `/signup` | POST | Register a new user |
| `/login` | POST | Authenticate a user |

### Example — Check Drug Interactions
```bash
curl -X POST http://localhost:3000/check-interactions \
  -H "Content-Type: application/json" \
  -d '{"medicines": ["warfarin", "aspirin"]}'

# Response:
{
  "warnings": [
    "Warning: Warfarin and Aspirin. Increased bleeding risk when combined."
  ]
}
```

### Example — Text-to-Speech
```bash
curl "http://localhost:3000/speak?text=Time+to+take+your+medication" \
  --output reminder.mp3
```

---

## 📦 Requirements

```
flask>=3.0.0
flask-cors>=4.0.0
flask-mail>=0.10.0
flask-apscheduler>=1.13.0
SpeechRecognition>=3.10.0
gTTS>=2.5.0
python-dotenv>=1.0.0
```

---

## 🚧 Challenges & Key Learnings

**Challenge 1 — DrugBank Access Denied**
Our initial plan to use the DrugBank licensed database was rejected. We pivoted to manually curating 36 medications from FDA OpenFDA, Mayo Clinic, Drugs.com, and MedlinePlus. This took significantly more time but gave us full control over data accuracy and structure.

**Challenge 2 — Interaction Checker Design**
Instead of a traditional binary interaction checker (safe/unsafe), we redesigned the system to display complete medication information including all interaction types. This more comprehensive approach is less alarmist and more empowering for users.

**Key Learnings**
- Adaptability is critical — a major data source pivot mid-project required rethinking the entire knowledge base architecture
- Modular API design enabled parallel development across backend and frontend teams
- Voice interfaces for accessibility require careful audio pipeline engineering — format conversion, noise handling, and streaming all add complexity

---

## 👥 Contributors

| Contributor | Role & Contributions |
|-------------|----------------------|
| **Yateen Sakhare** | AI/ML Backend — Flask REST API, Speech-to-Text (STT) pipeline, Text-to-Speech (TTS) audio streaming, Medication Knowledge Base curation (36 drugs from public sources), Drug Interaction Checker logic, Core business logic |
| **Jay Shah** | React Native Frontend — UI/UX design, medication management screens, Reminder & notification system, Email alert integration |

---

## ⚠️ Disclaimer

MedMind AI is a **prototype developed for academic purposes only**. It is not validated for clinical use and should not be used as a substitute for professional medical advice. Always consult a licensed healthcare provider before making medication decisions.

---

## 🏫 Academic Context

> Developed as a **Capstone Project 1** for the MS Artificial Intelligence & Machine Learning program at **Drexel University** (Summer 2025).

---

## 📚 References

1. OpenFDA API — https://open.fda.gov/
2. Mayo Clinic Drugs & Supplements — https://www.mayoclinic.org/drugs-supplements
3. Drugs.com — https://www.drugs.com/
4. MedlinePlus — https://medlineplus.gov/
5. gTTS Documentation — https://gtts.readthedocs.io/
6. SpeechRecognition — https://github.com/Uberi/speech_recognition
