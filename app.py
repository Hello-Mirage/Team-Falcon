"""Quizzy - Notes to Quiz Generator.
Full implementation of Core Requirements + Gamification (Streaks & XP System + Smart Mistakes Retry XP)
+ Google AI Studio (Gemini) API Integration with .env configuration and graceful local fallback
+ Flashcards Mode, Spaced Repetition (SM-2), and Shareable Quiz Links.
"""
import os
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, date, timedelta

# Auto-load .env configuration
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Fallback .env file loader in case python-dotenv is not installed
def _load_env_fallback():
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip().strip('"').strip("'")
                        if k and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

_load_env_fallback()

from flask import Flask, jsonify, request, send_from_directory
from extractor import extract_text_from_file
from quiz_generator import generate_quiz_from_notes
from gemini_generator import generate_quiz_with_gemini, is_ai_available, get_ai_status

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
            CREATE TABLE IF NOT EXISTS user_profile (
                id INTEGER PRIMARY KEY,
                total_xp INTEGER DEFAULT 0,
                current_streak INTEGER DEFAULT 0,
                longest_streak INTEGER DEFAULT 0,
                last_active_date TEXT,
                mistakes_solved_count INTEGER DEFAULT 0,
                quizzes_completed INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                word_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS quizzes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id INTEGER,
                title TEXT NOT NULL,
                question_type TEXT DEFAULT 'mixed',
                timer_seconds INTEGER DEFAULT 30,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER NOT NULL,
                concept TEXT NOT NULL,
                question_type TEXT NOT NULL,
                question_text TEXT NOT NULL,
                options_json TEXT, -- JSON array of strings
                correct_answer TEXT NOT NULL,
                explanation TEXT,
                source_sentence TEXT,
                FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL,
                percentage REAL NOT NULL,
                time_spent_seconds INTEGER DEFAULT 0,
                xp_earned INTEGER DEFAULT 0,
                is_retry INTEGER DEFAULT 0,
                weak_topics_json TEXT, -- JSON array of strings
                answers_json TEXT, -- detailed breakdown of user submissions
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS mistakes_bank (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                concept TEXT NOT NULL,
                question_type TEXT NOT NULL,
                question_text TEXT NOT NULL,
                options_json TEXT,
                correct_answer TEXT NOT NULL,
                explanation TEXT,
                user_wrong_answer TEXT,
                resolved INTEGER DEFAULT 0,
                resolved_at TIMESTAMP,
                interval_days INTEGER DEFAULT 1,
                ease_factor REAL DEFAULT 2.5,
                next_review_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Ensure singleton user profile exists
        profile = conn.execute("SELECT id FROM user_profile WHERE id = 1").fetchone()
        if not profile:
            conn.execute("""
                INSERT INTO user_profile (id, total_xp, current_streak, longest_streak, last_active_date)
                VALUES (1, 0, 0, 0, NULL)
            """)


init_db()


def update_gamification(conn, xp_to_add: int) -> dict:
    """Updates daily streak and total XP for user profile."""
    today = date.today().isoformat()
    profile = conn.execute("SELECT * FROM user_profile WHERE id = 1").fetchone()
    
    current_xp = profile["total_xp"]
    current_streak = profile["current_streak"]
    longest_streak = profile["longest_streak"]
    last_active = profile["last_active_date"]
    
    new_streak = current_streak
    streak_bonus_xp = 0
    is_new_day = False

    if not last_active:
        new_streak = 1
        is_new_day = True
    else:
        last_date = datetime.strptime(last_active, "%Y-%m-%d").date()
        today_date = date.today()
        diff = (today_date - last_date).days
        
        if diff == 1:
            new_streak = current_streak + 1
            streak_bonus_xp = 25  # Daily streak continuation bonus!
            is_new_day = True
        elif diff == 0:
            new_streak = current_streak
            is_new_day = False
        else:
            new_streak = 1
            is_new_day = True

    new_longest = max(longest_streak, new_streak)
    total_xp = current_xp + xp_to_add + streak_bonus_xp

    conn.execute("""
        UPDATE user_profile 
        SET total_xp = ?, 
            current_streak = ?, 
            longest_streak = ?, 
            last_active_date = ?,
            quizzes_completed = quizzes_completed + 1
        WHERE id = 1
    """, (total_xp, new_streak, new_longest, today))

    level = (total_xp // 100) + 1
    level_progress = total_xp % 100

    return {
        "total_xp": total_xp,
        "xp_earned": xp_to_add,
        "streak_bonus_xp": streak_bonus_xp,
        "current_streak": new_streak,
        "longest_streak": new_longest,
        "is_new_day": is_new_day,
        "level": level,
        "level_progress": level_progress
    }


@app.get("/")
def home():
    return send_from_directory(app.root_path, "index.html")


@app.get("/api/health")
def health():
    ai_status = get_ai_status()
    return jsonify(ok=True, ai=ai_status)


@app.get("/api/ai/status")
def api_ai_status():
    """Returns Google AI Studio / Gemini configuration status."""
    return jsonify(ok=True, **get_ai_status())


@app.get("/api/profile")
def api_profile():
    """Get player profile: Total XP, daily streak, mistakes count, and level stats."""
    with db() as conn:
        profile = conn.execute("SELECT * FROM user_profile WHERE id = 1").fetchone()
        unresolved_mistakes = conn.execute("SELECT COUNT(*) as cnt FROM mistakes_bank WHERE resolved = 0").fetchone()["cnt"]
        total_attempts = conn.execute("SELECT COUNT(*) as cnt FROM attempts").fetchone()["cnt"]
        
        total_xp = profile["total_xp"]
        level = (total_xp // 100) + 1
        level_progress = total_xp % 100
        
        return jsonify({
            "ok": True,
            "total_xp": total_xp,
            "current_streak": profile["current_streak"],
            "longest_streak": profile["longest_streak"],
            "last_active_date": profile["last_active_date"],
            "mistakes_solved_count": profile["mistakes_solved_count"],
            "unresolved_mistakes": unresolved_mistakes,
            "quizzes_completed": profile["quizzes_completed"],
            "total_attempts": total_attempts,
            "level": level,
            "level_progress": level_progress
        })


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


@app.route("/api/notes", methods=['GET', 'POST'])
def ep1_api_notes(**kwargs):
    if request.method == "GET":
        try:
            with db() as conn:
                rows = conn.execute(
                    "SELECT id, title, content, word_count, created_at FROM notes ORDER BY created_at DESC, id DESC"
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
        word_count = len(content.split())

        with db() as conn:
            cursor = conn.execute(
                "INSERT INTO notes (title, content, word_count) VALUES (?, ?, ?)",
                (title, content, word_count)
            )
            note_id = cursor.lastrowid
            row = conn.execute(
                "SELECT id, title, content, word_count, created_at FROM notes WHERE id = ?",
                (note_id,)
            ).fetchone()
            new_note = dict(row)

        return jsonify(ok=True, note=new_note), 201
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500


@app.route("/api/notes/<int:note_id>", methods=['DELETE'])
def api_delete_note(note_id):
    """Delete a saved note."""
    with db() as conn:
        conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    return jsonify(ok=True)


@app.route("/api/quiz", methods=['POST'])
def api_quiz():
    """Generates a quiz from notes content or existing note_id, saves it to SQLite, and returns questions.
    Uses Google AI Studio (Gemini) if configured in .env, with automatic fallback to local rule-based engine.
    """
    data = request.get_json(silent=True) or {}
    note_id = data.get("note_id")
    title = (data.get("title") or "").strip() or "Custom Study Quiz"
    content = (data.get("content") or "").strip()
    question_type = data.get("question_type") or "mixed"
    count = int(data.get("count") or 5)
    timer_seconds = int(data.get("timer_seconds") if data.get("timer_seconds") is not None else 30)

    # If note_id is provided, retrieve content
    if note_id and not content:
        with db() as conn:
            row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
            if row:
                content = row["content"]
                if not title or title == "Custom Study Quiz":
                    title = row["title"]

    if not content:
        return jsonify(ok=False, error="No note text provided to generate questions."), 400

    # Auto-save note if it was pasted directly
    with db() as conn:
        if not note_id:
            words = len(content.split())
            cur = conn.execute(
                "INSERT INTO notes (title, content, word_count) VALUES (?, ?, ?)",
                (title, content, words)
            )
            note_id = cur.lastrowid

        # 1. Attempt AI Generation with Google AI Studio (Gemini) if available
        raw_questions = None
        generation_source = "local"

        if is_ai_available():
            try:
                raw_questions = generate_quiz_with_gemini(
                    content,
                    title=title,
                    question_type=question_type,
                    count=count
                )
                if raw_questions:
                    generation_source = "google_ai_studio"
            except Exception as e:
                app.logger.warning(f"Google AI Studio generation failed: {e}. Falling back to local engine.")

        # 2. Fallback to local rule-based NLP generator if AI unavailable or returned None
        if not raw_questions:
            raw_questions = generate_quiz_from_notes(
                content,
                title=title,
                question_type=question_type,
                count=count
            )
            generation_source = "local_rule_based"

        if not raw_questions:
            return jsonify(
                ok=False,
                error="Could not extract enough concepts to form questions. Try adding more detailed notes or full sentences."
            ), 400

        # Save quiz to DB
        cur = conn.execute(
            "INSERT INTO quizzes (note_id, title, question_type, timer_seconds) VALUES (?, ?, ?, ?)",
            (note_id, title, question_type, timer_seconds)
        )
        quiz_id = cur.lastrowid

        saved_questions = []
        for q in raw_questions:
            options_str = json.dumps(q.get("options", []))
            q_cur = conn.execute("""
                INSERT INTO questions (quiz_id, concept, question_type, question_text, options_json, correct_answer, explanation, source_sentence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (quiz_id, q["concept"], q["question_type"], q["question_text"], options_str, q["correct_answer"], q["explanation"], q.get("source_sentence", "")))
            
            saved_questions.append({
                "id": q_cur.lastrowid,
                "quiz_id": quiz_id,
                "concept": q["concept"],
                "question_type": q["question_type"],
                "question_text": q["question_text"],
                "options": q.get("options", []),
                "correct_answer": q["correct_answer"],
                "explanation": q["explanation"],
                "source_sentence": q.get("source_sentence", "")
            })

    return jsonify({
        "ok": True,
        "quiz_id": quiz_id,
        "title": title,
        "timer_seconds": timer_seconds,
        "questions": saved_questions,
        "generation_source": generation_source,
        "ai_powered": (generation_source == "google_ai_studio")
    })


@app.route("/api/quiz/<int:qid>", methods=['GET'])
def api_get_quiz(qid):
    """Retrieve an existing quiz with all its questions for retaking or shareable quiz link."""
    with db() as conn:
        quiz = conn.execute("SELECT * FROM quizzes WHERE id = ?", (qid,)).fetchone()
        if not quiz:
            return jsonify(ok=False, error="Quiz not found."), 404
        
        q_rows = conn.execute("SELECT * FROM questions WHERE quiz_id = ?", (qid,)).fetchall()
        questions = []
        for r in q_rows:
            questions.append({
                "id": r["id"],
                "quiz_id": qid,
                "concept": r["concept"],
                "question_type": r["question_type"],
                "question_text": r["question_text"],
                "options": json.loads(r["options_json"]) if r["options_json"] else [],
                "correct_answer": r["correct_answer"],
                "explanation": r["explanation"],
                "source_sentence": r["source_sentence"] or ""
            })
            
        return jsonify({
            "ok": True,
            "quiz_id": qid,
            "title": quiz["title"],
            "timer_seconds": quiz["timer_seconds"],
            "question_type": quiz["question_type"],
            "questions": questions
        })


@app.route("/api/quiz/<int:qid>/submit", methods=['POST'])
def api_quiz_submit(qid):
    """Submits answers for quiz, checks correctness, identifies weak topics,
    stores mistakes in the Mistakes Bank, awards XP, and updates streak.
    """
    data = request.get_json(silent=True) or {}
    user_answers = data.get("answers", {})  # map of question_id (str/int) -> user_answer
    time_spent = int(data.get("time_spent_seconds", 0))
    is_retry = 1 if data.get("is_retry") else 0

    with db() as conn:
        quiz = conn.execute("SELECT * FROM quizzes WHERE id = ?", (qid,)).fetchone()
        if not quiz:
            return jsonify(ok=False, error="Quiz not found."), 404

        q_rows = conn.execute("SELECT * FROM questions WHERE quiz_id = ?", (qid,)).fetchall()
        if not q_rows:
            return jsonify(ok=False, error="Quiz has no questions."), 400

        total = len(q_rows)
        score = 0
        detailed_results = []
        weak_topics = set()
        topic_stats = {}  # concept -> {total, wrong}

        for row in q_rows:
            q_id = str(row["id"])
            concept = row["concept"]
            correct = row["correct_answer"].strip()
            user_ans = str(user_answers.get(q_id, "")).strip()
            q_type = row["question_type"]

            if concept not in topic_stats:
                topic_stats[concept] = {"total": 0, "wrong": 0}
            topic_stats[concept]["total"] += 1

            # Grade answer: case-insensitive match
            is_correct = (user_ans.lower() == correct.lower())

            if is_correct:
                score += 1
            else:
                weak_topics.add(concept)
                topic_stats[concept]["wrong"] += 1
                
                # Save mistake to mistakes bank
                options_str = row["options_json"]
                conn.execute("""
                    INSERT INTO mistakes_bank (quiz_id, question_id, concept, question_type, question_text, options_json, correct_answer, explanation, user_wrong_answer)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (qid, row["id"], concept, q_type, row["question_text"], options_str, correct, row["explanation"], user_ans))

            detailed_results.append({
                "question_id": row["id"],
                "concept": concept,
                "question_type": q_type,
                "question_text": row["question_text"],
                "options": json.loads(row["options_json"]) if row["options_json"] else [],
                "user_answer": user_ans,
                "correct_answer": correct,
                "is_correct": is_correct,
                "explanation": row["explanation"]
            })

        percentage = round((score / total) * 100, 1) if total > 0 else 0
        weak_topics_list = list(weak_topics)

        # Gamification: XP calculation
        # 10 XP per correct question + 50 XP bonus for perfect score
        base_xp = score * 10
        perfect_bonus = 50 if (score == total and total > 0) else 0
        earned_xp = base_xp + perfect_bonus

        gamification_info = update_gamification(conn, earned_xp)

        # Save attempt
        conn.execute("""
            INSERT INTO attempts (quiz_id, score, total, percentage, time_spent_seconds, xp_earned, is_retry, weak_topics_json, answers_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (qid, score, total, percentage, time_spent, earned_xp, is_retry, json.dumps(weak_topics_list), json.dumps(detailed_results)))

    return jsonify({
        "ok": True,
        "quiz_id": qid,
        "score": score,
        "total": total,
        "percentage": percentage,
        "weak_topics": weak_topics_list,
        "topic_breakdown": topic_stats,
        "results": detailed_results,
        "gamification": gamification_info
    })


# ---- MISTAKES BANK & SPACED REPETITION (SM-2) -----------------------------
@app.get("/api/mistakes")
def api_mistakes_list():
    """Retrieve all unresolved mistakes for the player to practice and earn XP."""
    with db() as conn:
        rows = conn.execute("""
            SELECT * FROM mistakes_bank 
            WHERE resolved = 0 
            ORDER BY id DESC
        """).fetchall()
        
        mistakes = []
        for r in rows:
            m = dict(r)
            m["options"] = json.loads(m["options_json"]) if m["options_json"] else []
            mistakes.append(m)
            
        return jsonify(ok=True, mistakes=mistakes, count=len(mistakes))


@app.post("/api/mistakes/resolve")
def api_mistakes_resolve():
    """Revisit and solve a previous mistake with SM-2 Spaced Repetition.
    Awards +10 to +20 XP based on rating ('hard', 'good', 'easy') and marks it resolved!
    """
    data = request.get_json(silent=True) or {}
    mistake_id = data.get("mistake_id")
    user_answer = str(data.get("user_answer", "")).strip()
    rating = str(data.get("rating", "good")).lower()  # "hard", "good", "easy"

    if not mistake_id or not user_answer:
        return jsonify(ok=False, error="mistake_id and user_answer are required."), 400

    with db() as conn:
        row = conn.execute("SELECT * FROM mistakes_bank WHERE id = ? AND resolved = 0", (mistake_id,)).fetchone()
        if not row:
            return jsonify(ok=False, error="Mistake not found or already resolved."), 404

        correct = row["correct_answer"].strip()
        is_correct = (user_answer.lower() == correct.lower())

        if is_correct:
            # SM-2 intervals: Hard -> 1 day, Good -> 3 days, Easy -> 7 days
            interval_map = {"hard": 1, "good": 3, "easy": 7}
            interval = interval_map.get(rating, 3)
            next_review = (date.today() + timedelta(days=interval)).isoformat()
            
            xp_map = {"hard": 10, "good": 15, "easy": 20}
            xp_reward = xp_map.get(rating, 15)
            
            now = datetime.now().isoformat()
            conn.execute("""
                UPDATE mistakes_bank 
                SET resolved = 1, resolved_at = ?, interval_days = ?, next_review_date = ?
                WHERE id = ?
            """, (now, interval, next_review, mistake_id))
            conn.execute("UPDATE user_profile SET mistakes_solved_count = mistakes_solved_count + 1 WHERE id = 1")
            
            gamification_info = update_gamification(conn, xp_reward)
            
            return jsonify({
                "ok": True,
                "is_correct": True,
                "message": f"Correct! Mastered with '{rating.capitalize()}' (+{xp_reward} XP). Next review in {interval} days.",
                "xp_earned": xp_reward,
                "interval_days": interval,
                "next_review_date": next_review,
                "explanation": row["explanation"],
                "gamification": gamification_info
            })
        else:
            return jsonify({
                "ok": True,
                "is_correct": False,
                "message": "Not quite right yet. Review the explanation and try again!",
                "correct_answer": correct,
                "explanation": row["explanation"]
            })


# ---- FLASHCARD MODE GAMIFICATION XP ---------------------------------------
@app.post("/api/flashcards/xp")
def api_flashcards_xp():
    """Awards XP for active flashcard self-testing."""
    data = request.get_json(silent=True) or {}
    xp = int(data.get("xp", 10))
    with db() as conn:
        gamification_info = update_gamification(conn, xp)
    return jsonify(ok=True, xp_earned=xp, gamification=gamification_info)


# ---- HISTORY & ATTEMPTS ---------------------------------------------------
@app.route("/api/history", methods=['GET'])
def api_history():
    """Returns past attempts, scores, and diagnostics."""
    with db() as conn:
        rows = conn.execute("""
            SELECT a.*, q.title as quiz_title, q.question_type 
            FROM attempts a
            JOIN quizzes q ON a.quiz_id = q.id
            ORDER BY a.id DESC
            LIMIT 50
        """).fetchall()

        history = []
        for r in rows:
            item = dict(r)
            item["weak_topics"] = json.loads(item["weak_topics_json"]) if item["weak_topics_json"] else []
            history.append(item)

        return jsonify(ok=True, history=history)


@app.route("/api/history/<int:attempt_id>", methods=['DELETE'])
def api_delete_history(attempt_id):
    """Delete a past attempt record."""
    with db() as conn:
        conn.execute("DELETE FROM attempts WHERE id = ?", (attempt_id,))
    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
