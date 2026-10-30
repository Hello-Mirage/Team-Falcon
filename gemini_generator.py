"""Google AI Studio (Gemini) Quiz Generator.
Connects to Google AI Studio API using GEMINI_API_KEY or GOOGLE_API_KEY from .env
to generate context-aware MCQs and fill-in-the-blank questions from study notes.
"""
import os
import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-1.5-flash"
API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def get_api_key() -> str:
    """Retrieve Google AI Studio / Gemini API key from environment."""
    return (
        os.environ.get("GEMINI_API_KEY", "").strip()
        or os.environ.get("GOOGLE_API_KEY", "").strip()
    )


def get_model() -> str:
    """Retrieve configured Gemini model name."""
    return os.environ.get("GEMINI_MODEL", "").strip() or DEFAULT_MODEL


def is_ai_available() -> bool:
    """Check if a valid Gemini API key is configured."""
    key = get_api_key()
    return bool(key and len(key) > 10 and not key.startswith("your_"))


def get_ai_status() -> dict:
    """Return status dictionary about Google AI Studio integration."""
    has_key = is_ai_available()
    key = get_api_key()
    key_preview = f"{key[:6]}...{key[-4:]}" if (has_key and len(key) >= 10) else None
    return {
        "provider": "Google AI Studio",
        "configured": has_key,
        "model": get_model(),
        "key_preview": key_preview
    }


def _build_quiz_prompt(text: str, title: str = "", question_type: str = "mixed", count: int = 5) -> str:
    """Constructs prompt for Gemini with structured JSON output instructions."""
    type_instruction = {
        "mcq": "Generate ONLY multiple-choice questions (4 options per question).",
        "fill_blank": "Generate ONLY fill-in-the-blank questions (use '__________' for the missing term).",
        "mixed": "Generate a balanced mix of multiple-choice and fill-in-the-blank questions."
    }.get(question_type, "Generate a balanced mix of multiple-choice and fill-in-the-blank questions.")

    prompt = f"""You are an expert educator and active-recall test generator.
Analyze the following study notes and generate exactly {count} high-yield study questions.

Target Topic Title: {title or 'Study Notes'}
Question Mode: {type_instruction}

Study Notes:
\"\"\"
{text}
\"\"\"

Guidelines:
1. Focus on core concepts, definitions, formulas, relationships, and key facts.
2. For multiple-choice questions ('mcq'):
   - 'question_text': Clear, unambiguous question stem.
   - 'options': Exactly 4 distinct options. One is the correct answer; the other 3 are plausible, realistic distractors related to the topic. Do NOT use "All of the above" or "None of the above".
   - 'correct_answer': Must exactly match one of the 4 items in 'options'.
3. For fill-in-the-blank questions ('fill_blank'):
   - 'question_text': A statement where the key term is replaced by '__________'.
   - 'options': An empty array [].
   - 'correct_answer': The exact missing term or short phrase.
4. 'concept': A concise 2-4 word topic or subtopic label (e.g. "Krebs Cycle", "Quicksort Complexity", "Mitochondrial Matrix"). This is used for weak topic diagnosis.
5. 'explanation': Educational 1-2 sentence explanation of why the answer is correct and why the distractors are wrong.
6. 'source_sentence': The quote or sentence from the notes this question tests.

Return a JSON array containing exactly {count} objects matching this JSON schema:
[
  {{
    "question_type": "mcq" | "fill_blank",
    "concept": "Topic Name",
    "question_text": "Question text here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Option A",
    "explanation": "Why this answer is correct...",
    "source_sentence": "Sentence from notes..."
  }}
]
Do not wrap in markdown tags like ```json. Return ONLY the raw JSON array.
"""
    return prompt.strip()


def generate_quiz_with_gemini(text: str, title: str = "", question_type: str = "mixed", count: int = 5) -> list[dict] | None:
    """Calls Google AI Studio Gemini API to generate questions from study notes.
    Returns a list of standardized question dicts, or None if API is unavailable or fails.
    """
    api_key = get_api_key()
    if not is_ai_available():
        logger.info("Google AI Studio API key not configured. Falling back to local generator.")
        return None

    model = get_model()
    prompt = _build_quiz_prompt(text, title=title, question_type=question_type, count=count)

    # Models to attempt (configured model first, then fallback)
    models_to_try = [model]
    for fallback in ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]:
        if fallback not in models_to_try:
            models_to_try.append(fallback)

    last_error = None

    for current_model in models_to_try:
        url = f"{API_BASE_URL}/{current_model}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.35,
                "responseMimeType": "application/json"
            }
        }

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=req_data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=25) as response:
                status_code = response.getcode()
                raw_response = response.read().decode("utf-8")

                if status_code != 200:
                    logger.warning(f"Google AI Studio model {current_model} returned HTTP {status_code}")
                    continue

                res_json = json.loads(raw_response)
                candidates = res_json.get("candidates", [])
                if not candidates:
                    logger.warning(f"No candidates returned by Gemini model {current_model}")
                    continue

                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    continue

                content_text = parts[0].get("text", "").strip()
                if not content_text:
                    continue

                # Strip possible markdown code block fences if present
                if content_text.startswith("```"):
                    lines = content_text.splitlines()
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    content_text = "\n".join(lines).strip()

                parsed_data = json.loads(content_text)
                if isinstance(parsed_data, dict):
                    # In case the model wrapped it in {"questions": [...]}
                    for k in ["questions", "quiz", "data", "items"]:
                        if k in parsed_data and isinstance(parsed_data[k], list):
                            parsed_data = parsed_data[k]
                            break

                if not isinstance(parsed_data, list):
                    logger.warning("Gemini did not return a JSON array.")
                    continue

                # Standardize questions
                standardized = []
                for q in parsed_data:
                    if not isinstance(q, dict):
                        continue
                    q_text = str(q.get("question_text", "")).strip()
                    correct = str(q.get("correct_answer", "")).strip()
                    concept = str(q.get("concept", "")).strip() or (title or "Key Concepts")
                    q_type = q.get("question_type", "mcq")
                    if q_type not in ["mcq", "fill_blank"]:
                        q_type = "mcq"

                    raw_options = q.get("options", [])
                    options = [str(o).strip() for o in raw_options if str(o).strip()]

                    if q_type == "mcq":
                        # Ensure correct answer is one of the options
                        if correct and correct not in options:
                            options.append(correct)
                        # Ensure 4 options
                        while len(options) < 4:
                            options.append(f"Related factor {len(options) + 1}")
                        options = options[:4]
                    else:
                        options = []

                    explanation = str(q.get("explanation", "")).strip() or f"Correct answer is {correct}."
                    source_sentence = str(q.get("source_sentence", "")).strip()

                    if q_text and correct:
                        standardized.append({
                            "question_type": q_type,
                            "concept": concept,
                            "question_text": q_text,
                            "options": options,
                            "correct_answer": correct,
                            "explanation": explanation,
                            "source_sentence": source_sentence,
                            "generated_by": f"Google AI Studio ({current_model})"
                        })

                if standardized:
                    logger.info(f"Successfully generated {len(standardized)} questions with {current_model}")
                    return standardized[:count]

        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")
            except Exception:
                pass
            logger.error(f"Google AI Studio HTTPError {e.code} on {current_model}: {error_body}")
            last_error = e
        except Exception as e:
            logger.error(f"Error calling Google AI Studio {current_model}: {e}")
            last_error = e

    logger.warning(f"All Gemini models failed or key invalid. Last error: {last_error}")
    return None

