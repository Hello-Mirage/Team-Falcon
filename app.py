"""Notes to Quiz Generator - Hack Day Haldia x GRID community starter. Build the core tasks from README.md."""
import os
import sqlite3
from contextlib import contextmanager

from flask import Flask, jsonify, request, send_from_directory
from extractor import extract_text_from_file

app = Flask(__name__, static_folder="static")
DB_PATH = os.path.join(app.root_path, "data.db")


@contextmanager
def db():
    """SQLite connection generator with auto-commit, rollback on error, and proper close.
    Use: with db() as conn: ...
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS quizzes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id INTEGER,
                title TEXT NOT NULL,
                question_type TEXT,
                timer_seconds INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER NOT NULL,
                question_type TEXT,
                question_text TEXT NOT NULL,
                options TEXT,
                correct_answer TEXT,
                explanation TEXT,
                topic TEXT,
                FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER NOT NULL,
                score REAL,
                total REAL,
                time_spent_seconds INTEGER,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS attempt_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attempt_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                user_answer TEXT,
                is_correct BOOLEAN,
                FOREIGN KEY (attempt_id) REFERENCES attempts(id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
            );
        """)


init_db()


@app.get("/")
def home():
    return send_from_directory(app.root_path, "index.html")


@app.get("/api/health")
def health():
    return jsonify(ok=True)


@app.post("/api/upload")
def api_upload():
    if "file" not in request.files:
        return jsonify(ok=False, error="No file uploaded."), 400
    file = request.files["file"]
    if not file or not file.filename:
        return jsonify(ok=False, error="No file selected."), 400

    result = extract_text_from_file(file, file.filename)
    status_code = 200 if result.get("ok") else 400
    return jsonify(result), status_code


# ---- TODO(core): fill these in ------------------------------------------
@app.route("/api/notes", methods=['GET', 'POST'])
def ep1_api_notes(**kwargs):
    if request.method == "GET":
        try:
            with db() as conn:
                rows = conn.execute(
                    "SELECT id, title, content, created_at FROM notes ORDER BY created_at DESC, id DESC"
                ).fetchall()
                notes = [dict(row) for row in rows]
            return jsonify(ok=True, notes=notes), 200
        except Exception as e:
            return jsonify(ok=False, error=str(e)), 500

    # POST
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(ok=False, error="Invalid JSON payload. Expected a JSON object."), 400

        title = data.get("title")
        content = data.get("content")

        if not title or not isinstance(title, str) or not title.strip():
            return jsonify(ok=False, error="Title is required and cannot be empty."), 400

        if not content or not isinstance(content, str) or not content.strip():
            return jsonify(ok=False, error="Content is required and cannot be empty."), 400

        title = title.strip()
        content = content.strip()

        with db() as conn:
            cursor = conn.execute(
                "INSERT INTO notes (title, content) VALUES (?, ?)",
                (title, content)
            )
            note_id = cursor.lastrowid
            row = conn.execute(
                "SELECT id, title, content, created_at FROM notes WHERE id = ?",
                (note_id,)
            ).fetchone()
            new_note = dict(row)

        return jsonify(ok=True, note=new_note), 201
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500


@app.route("/api/quiz", methods=['POST'])
def ep2_api_quiz(**kwargs):
    # TODO(core): notes -> list of questions
    return jsonify(error="not implemented"), 501


@app.route("/api/quiz/<int:qid>/submit", methods=['POST'])
def ep3_api_quiz_int_qid_submit(**kwargs):
    # TODO(core): answers -> score + weak topics
    return jsonify(error="not implemented"), 501


@app.route("/api/history", methods=['GET'])
def ep4_api_history(**kwargs):
    # TODO(core): past attempts
    return jsonify(error="not implemented"), 501



if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
