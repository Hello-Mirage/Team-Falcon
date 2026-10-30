"""Quiz generation engine: extracts concepts, sentences, and keywords from notes
to generate multiple-choice and fill-in-the-blank questions with plausible distractors.
"""
import re
import random
import string

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can",
    "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't",
    "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have",
    "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him",
    "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't",
    "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor",
    "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out",
    "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some",
    "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there",
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those", "through", "to",
    "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's",
    "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're",
    "you've", "your", "yours", "yourself", "yourselves", "also", "using", "used", "which", "whose", "within",
    "without", "along", "due", "into", "onto", "upon", "overall", "typically", "general", "generally"
}


def clean_text(text: str) -> str:
    """Normalize whitespace and remove markdown/formatting noise."""
    text = re.sub(r'[\r\t]', ' ', text)
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()


def extract_sentences(text: str) -> list[str]:
    """Break text into informative, standalone sentences."""
    cleaned = clean_text(text)
    # Split by standard sentence terminators (. ! ? or newline)
    raw_sentences = re.split(r'(?<=[.!?])\s+|\n+', cleaned)
    valid_sentences = []
    
    for s in raw_sentences:
        s = s.strip().strip("-*•# ")
        if len(s) < 25:
            continue
        # Check if sentence has enough informative words
        words = [w for w in re.findall(r'[A-Za-z0-9_-]+', s) if w.lower() not in STOPWORDS]
        if len(words) >= 3:
            valid_sentences.append(s)
            
    return valid_sentences


def extract_key_terms(text: str) -> list[str]:
    """Extract candidate key phrases, capitalized terms, technical words, and definitions."""
    terms = set()
    
    # 1. Look for acronyms or capitalized compound terms (e.g. ATP, Big-O, Cristae)
    caps_matches = re.findall(r'\b[A-Z][A-Za-z0-9\'-]+(?:\s+[A-Z][A-Za-z0-9\'-]+)*\b', text)
    for match in caps_matches:
        if match.lower() not in STOPWORDS and len(match) > 2:
            terms.add(match)

    # 2. Look for terms in quotes or parentheses (e.g. "Krebs cycle", (ATP))
    paren_matches = re.findall(r'[\"\']([A-Za-z0-9\s\-]+)[\"\']|\(([A-Za-z0-9\s\-]{2,30})\)', text)
    for m1, m2 in paren_matches:
        term = (m1 or m2).strip()
        if term.lower() not in STOPWORDS and 2 < len(term) < 35:
            terms.add(term)

    # 3. Look for definition patterns: "X is ...", "X are ...", "X refers to ..."
    def_matches = re.findall(r'([A-Z][A-Za-z0-9\s\-]{1,30})\s+(?:is|are|refers to|means|represents)\b', text)
    for m in def_matches:
        term = m.strip()
        if term.lower() not in STOPWORDS and 2 < len(term) < 35:
            terms.add(term)

    # 4. Significant non-stopword tokens (4+ letters)
    tokens = [w for w in re.findall(r'\b[A-Za-z]{4,}\b', text) if w.lower() not in STOPWORDS]
    for t in tokens:
        terms.add(t)

    # Filter out pure numbers or single characters
    clean_terms = []
    for t in terms:
        t_clean = t.strip()
        if len(t_clean) >= 3 and not t_clean.isdigit():
            clean_terms.append(t_clean)
            
    return clean_terms


def infer_concept(sentence: str, title: str = "") -> str:
    """Infer an overarching concept or topic label from a sentence."""
    # Check for definition subject
    match = re.match(r'^([A-Z][A-Za-z0-9\s\-]{2,25})\s+(?:is|are|was|were|refers to|contains|provides|occurs)', sentence)
    if match:
        return match.group(1).strip()
    
    # Check if title has a relevant keyword
    if title:
        parts = [p.strip() for p in re.split(r'[:\-–,&|]', title) if p.strip()]
        if parts:
            for p in parts:
                if any(w.lower() in sentence.lower() for w in p.split() if w.lower() not in STOPWORDS):
                    return p
            return parts[0]
            
    # Default to first 3 words
    words = sentence.split()
    return " ".join(words[:2]).strip(string.punctuation)


def generate_mcq(sentence: str, all_terms: list[str], title: str = "") -> dict | None:
    """Generate a multiple-choice question from a sentence by finding the key subject/term."""
    # Find candidate terms within this sentence
    candidates = []
    for term in all_terms:
        # Match as whole word/phrase
        pattern = r'\b' + re.escape(term) + r'\b'
        match = re.search(pattern, sentence, re.IGNORECASE)
        if match:
            # Score candidate: preference to capitalized / technical / longer terms
            score = len(term) + (10 if term[0].isupper() else 0)
            candidates.append((score, match.group(0), term))
            
    if not candidates:
        return None
        
    # Sort candidates by score descending
    candidates.sort(reverse=True, key=lambda x: x[0])
    _, matched_str, base_term = candidates[0]
    
    # The correct answer is the matched term (preserved casing or title case)
    correct_answer = matched_str.strip()
    
    # Create question stem by replacing term or framing as question
    pattern = r'\b' + re.escape(matched_str) + r'\b'
    cloze_sentence = re.sub(pattern, "__________", sentence, count=1, flags=re.IGNORECASE)
    
    question_text = f"According to the notes: \"{cloze_sentence}\"\nWhich term best completes this statement?"
    concept = infer_concept(sentence, title)
    
    # Build distractors from other terms in notes
    distractor_pool = [
        t for t in all_terms 
        if t.lower() != correct_answer.lower() 
        and abs(len(t) - len(correct_answer)) <= 15
        and t.lower() not in sentence.lower()
    ]
    
    # Generic backup distractors if note terms are scarce
    generic_distractors = [
        "Metabolic Flux", "Synthesis Factor", "Catalytic Substrate", "Ribosomal Index",
        "Kinematic Vector", "Dynamic Array", "Recursion Tree", "Entropy Gradient",
        "Industrial Charter", "Monetary Coefficient", "Electrochemical Potential"
    ]
    
    selected_distractors = []
    if len(distractor_pool) >= 3:
        selected_distractors = random.sample(distractor_pool, 3)
    else:
        selected_distractors = distractor_pool[:]
        for g in generic_distractors:
            if len(selected_distractors) >= 3:
                break
            if g.lower() != correct_answer.lower() and g not in selected_distractors:
                selected_distractors.append(g)
                
    options = selected_distractors[:3] + [correct_answer]
    random.shuffle(options)
    
    explanation = f"Correct answer is '{correct_answer}'. Context: \"{sentence}\""
    
    return {
        "question_type": "mcq",
        "concept": concept,
        "question_text": question_text,
        "options": options,
        "correct_answer": correct_answer,
        "explanation": explanation,
        "source_sentence": sentence
    }


def generate_fill_blank(sentence: str, all_terms: list[str], title: str = "") -> dict | None:
    """Generate a fill-in-the-blank question from a sentence."""
    candidates = []
    for term in all_terms:
        pattern = r'\b' + re.escape(term) + r'\b'
        match = re.search(pattern, sentence, re.IGNORECASE)
        if match:
            score = len(term) + (10 if term[0].isupper() else 0)
            candidates.append((score, match.group(0), term))
            
    if not candidates:
        return None
        
    candidates.sort(reverse=True, key=lambda x: x[0])
    _, matched_str, base_term = candidates[0]
    correct_answer = matched_str.strip()
    
    pattern = r'\b' + re.escape(matched_str) + r'\b'
    blank_sentence = re.sub(pattern, "__________", sentence, count=1, flags=re.IGNORECASE)
    
    question_text = f"Fill in the blank: {blank_sentence}"
    concept = infer_concept(sentence, title)
    explanation = f"The missing key term is '{correct_answer}'. Original note: \"{sentence}\""
    
    return {
        "question_type": "fill_blank",
        "concept": concept,
        "question_text": question_text,
        "options": [],
        "correct_answer": correct_answer,
        "explanation": explanation,
        "source_sentence": sentence
    }


def generate_quiz_from_notes(text: str, title: str = "General Study", question_type: str = "mixed", count: int = 5) -> list[dict]:
    """Extract concepts and generate specified number of questions."""
    sentences = extract_sentences(text)
    if not sentences:
        # Fallback: if short text, split by punctuation
        raw_words = text.split()
        if len(raw_words) >= 5:
            sentences = [text.strip()]
        else:
            return []
            
    all_terms = extract_key_terms(text)
    random.shuffle(sentences)
    
    questions = []
    seen_answers = set()
    
    # First pass: try generating questions for each sentence
    for s in sentences:
        if len(questions) >= count:
            break
            
        # Determine question type
        target_type = question_type
        if question_type == "mixed":
            target_type = "mcq" if (len(questions) % 2 == 0) else "fill_blank"
            
        q = None
        if target_type == "mcq":
            q = generate_mcq(s, all_terms, title)
            if not q:
                q = generate_fill_blank(s, all_terms, title)
        else:
            q = generate_fill_blank(s, all_terms, title)
            if not q:
                q = generate_mcq(s, all_terms, title)
                
        if q and q["correct_answer"].lower() not in seen_answers:
            seen_answers.add(q["correct_answer"].lower())
            questions.append(q)
            
    # Second pass if not enough questions yet
    if len(questions) < count:
        for s in sentences:
            if len(questions) >= count:
                break
            q = generate_mcq(s, all_terms, title) or generate_fill_blank(s, all_terms, title)
            if q and q["question_text"] not in [x["question_text"] for x in questions]:
                questions.append(q)
                
    return questions[:count]

