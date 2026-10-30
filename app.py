"""Notes to Quiz Generator - Hack Day Haldia x GRID community starter. Build the core tasks from README.md."""
import os
import sqlite3

from flask import Flask, jsonify, request, send_from_directory
from extractor import extract_text_from_file

app = Flask(__name__, static_folder="static")
DB_PATH = os.path.join(app.root_path, "data.db")


def db():
    """SQLite connection whose rows behave like dicts. Use:  with db() as conn: ..."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.executescript("""
            -- TODO: create your tables here, for example:
            -- CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
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
    # TODO(core): list / save notes
    return jsonify(error="not implemented"), 501


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
