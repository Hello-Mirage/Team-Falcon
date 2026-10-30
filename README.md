# Notes to Quiz Generator

> Paste your notes, get a quiz, then learn from your mistakes.

Hack Day Haldia x GRID community - 6-hour build challenge

**Repo:** `team-falcon` | **Stack:** Python / Flask | **Difficulty:** Hard | **Time:** 6 hours

## Brief
Revision is passive. Build an app that turns pasted notes into questions and shows which topics need more work.

## Core tasks (must-do)
- [x] Paste notes; split them into concepts and key sentences
- [x] Generate MCQ and fill-in-the-blank questions with plausible distractors (rules or an AI model)
- [x] Quiz flow: one question at a time, timer, instant feedback
- [x] Score summary that highlights weak topics
- [x] Retry only the questions you got wrong
- [x] Persist notes, quizzes and attempts in SQLite (helper already in app.py)
- [x] UI to manage saved notes and past quizzes

## Bonus tasks (only after the core works)
- [x] Spaced-repetition review queue (SM-2)
- [x] Flashcard mode
- [x] Upload .txt / .pdf notes
- [x] Shareable quiz link

## What is already here
- `index.html` - base page that pings `/api/health`
- `app.py` - Flask app with a SQLite helper (`db()`, `init_db()`), `/api/health` and TODO endpoint stubs (they return 501 until you implement them)
- `requirements.txt` - `flask`, `gunicorn`

## Flutter Android App (`quizzy_app`)

Quizzy also includes a mobile Android application built with Flutter that allows you to record speech from your microphone, transcribe it in real time, and generate a quiz using Google AI Studio (Gemini API via your Quizzy backend).

### Features
- 🎙️ **Live Voice Recording & Transcription**: Tap the mic to record lectures, discussions, or personal notes. Speech is transcribed on-device in real time.
- ⚡ **Gemini-Powered Quiz Generation**: Transcripts are processed through the Quizzy backend with the `apinew` Gemini API key to produce MCQs and fill-in-the-blank questions.
- 🎯 **Interactive Quiz Flow**: One question at a time, interactive answer selection, instant green/red feedback with explanations, and concept tags.
- 🏆 **Scorecard & Weak Topics**: Results screen breaks down score percentage, grade, review list for incorrect questions, and highlights weak concepts.
- ⚙️ **Configurable Backend**: In-app Settings page lets you plug in your Render deployment URL and test connection with one tap.

### Running the App
```bash
cd quizzy_app
flutter pub get
flutter run
```

### Build APK
```bash
cd quizzy_app
flutter build apk --debug
```

## Run locally
```bash
pip install -r requirements.txt
python app.py   # then open http://127.0.0.1:5000
```

## Deploy
Any Python host works (for example Render or PythonAnywhere). Start command: `gunicorn app:app`. Free hosts may reset the filesystem on restart, so the SQLite file can reset - fine for a demo.

## Suggested pacing
- Hour 1: read this README, agree on a plan and split the work
- Hours 2-4: build the core tasks
- Hour 5: integrate, polish, then bonus tasks if time allows
- Hour 6: deploy, open the Pull Request, submit on the MLH platform (OrganizerHQ)

## Submission checklist
- [x] All core tasks work end to end
- [x] Project is deployed and the live link opens
- [ ] Pull Request created on the Voyage GitHub repository assigned to your team
- [ ] Project submitted on the MLH platform (OrganizerHQ) - instructions are shared at the start of the event

## Rules
- Build new features on top of this starter project and integrate them.
- Teams of 3-4; every member must be present.
- AI tools and open-source / open-weight models are fully allowed.
