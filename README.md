code to check words: from project_fixed import DictionaryClient; w=DictionaryClient().lookup('obey'); print(w.definitions)"
The word here is "obey", change it to check if the online dictionary is working

......still working on the GUI part

### Imports & File Paths

import re, json, random, requests
from datetime import datetime, date, timedelta
from pathlib import Path
#- `re` — for checking if a word is valid (no numbers, no symbols)
#- `json` — for saving/loading data as text files
#- `random` — for shuffling quiz questions
#- `requests` — for calling the Dictionary API over the internet
#- `datetime, date, timedelta` — for tracking when to review a word next
#- `pathlib.Path` — a clean way to work with file locations on your computer


DATA_DIR   = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
WORDS_FILE  = DATA_DIR / "saved_words.json"
SCORES_FILE = DATA_DIR / "quiz_scores.json"
SRS_FILE    = DATA_DIR / "srs_data.json"

#This creates a `data/` folder next to your app files (if it doesn't exist), and defines the three files where all user data gets saved. 
#Everything is stored as plain JSON text — no database needed.

### `validate_word(word)` — Input Checker
def validate_word(word):
    word = word.strip().lower()
    if not word:
        raise ValueError("Please enter a word.")
#This checks whether the variable word is empty. The keyword not means "if there is nothing."
#raise is used to manually create an exception (error).

    if not re.match(r"^[a-zA-Z'-]{1,50}$", word):
        raise ValueError(f"'{word}' doesn't look like a valid English word.")
    return word
#This line checks whether the word is valid using a regular expression (regex).
#The r means raw string.It tells Python to treat backslashes (\) as ordinary characters, which is useful when writing regular expressions.

#Before anything happens, this checks the user's input. It:
#1. Removes extra spaces and makes it lowercase
#2. Rejects empty input
#3. Uses a **regular expression** (`re.match`) to ensure only letters, hyphens, and apostrophes are allowed — no numbers, no `@#$` symbols, and max 50 characters
#4. Returns the cleaned word if everything is fine, or raises an error that the app can catch and show to the user


### Class: `Word` — A Word and All Its Info

class Word:
    def __init__(self, word, phonetic="", definitions=None,
                 examples=None, synonyms=None, antonyms=None, part_of_speech=""):
        self.word           = word
        self.phonetic       = phonetic
        self.definitions    = definitions or []
        ...

#This is a blueprint for storing everything about one word. When you look up "ephemeral", a `Word` object is created holding its pronunciation, definitions, example sentences, synonyms, and antonyms all in one place.


    def to_dict(self):
        #self refers to the current object.
        return self.__dict__
        #Every Python object stores its attributes in a dictionary called __dict__.

    @classmethod
    #This is called a decorator.
#It tells Python that the method belongs to the class, not an individual object.
#A class method is another way of creating an object.
    def from_dict(cls, d):
       # This means
        #cls = the class itself (like Word)
       #d = dictionary
        return cls(**{k: v for k, v in d.items() if k in cls.__init__.__code__.co_varnames})
        #return cls here means to return word
        #Python loops through every key and value.(key and Value)

#- `to_dict()` converts the Word object into a plain Python dictionary so it can be saved as JSON
#- `from_dict()` does the reverse — reads a dictionary from the JSON file and reconstructs a Word object. 
#The `@classmethod` means you call it on the class itself: `Word.from_dict(data)` rather than on an instance



### Class: `Flashcard` — A Study Card
class Flashcard:
    def __init__(self, word, definition, example="", memory_trick="", simple_explanation=""):

#Very similar structure to `Word`, but focused on what you need for studying: just the word, its definition, an example sentence, 
#and optionally an AI-generated memory trick and simple explanation. It also has `to_dict()` and `from_dict()` for saving.
#to_dict() converts an object into a dictionary so it can be saved as JSON.
#@classmethod creates a method that belongs to the class instead of an object.
#from_dict() takes a dictionary and recreates an object from it.
#d.items() loops through each key-value pair in the dictionary.
#if k in cls.__init__.__code__.co_varnames ignores any keys that aren't accepted by the class constructor.
#**dictionary unpacks the dictionary so its keys become named arguments when creating the object.

### Class: `DictionaryClient` — Fetches Word Data from the Internet
class DictionaryClient:
#DictionaryClient class is responsible for:
#-Connecting to the online dictionary API.
#-Sending a word to the API.
#-Receiving the definition and other information.
#It's a messenger between your Python program and the online dictionary.

    URL = "https://api.dictionaryapi.dev/api/v2/entries/en/"
    #This stores the base url of the online dictionary API
    def lookup(self, raw_word):
        #This defines the method lookup(), which accepts two parameters, self and raw_word
        #self refers to the instance of the class that is calling the method. 
        #raw_word is the word that the user wants to look up.
        word = validate_word(raw_word)
        #First, it validates the input word using the validate_word() function we defined earlier.
        #The validate_word() function might:
        #Remove leading and trailing spaces.
        #Convert the word to lowercase.
        #Check that it contains only valid English letters.
        try:
        #This class has one job: ask the Free Dictionary API for a word's data. It:
#1. Validates the word first
#2. Makes an HTTP GET request (like visiting a website, but for data)
#3. Catches specific errors — if there's no internet it says so, if it's too slow it times out cleanly
            r = requests.get(self.URL + word, timeout=8)
            #This sends an HTTP GET request to the Free Dictionary API.
            #Timeout=8 means it will wait 8 seconds for a response before giving up.
        if r.status_code == 404:
            # checks whether the web server returned a 404 status code, which means "Not Found."
            raise LookupError(f"'{word}' was not found in the dictionary.")
        if r.status_code != 200:
            raise RuntimeError(f"API error (HTTP {r.status_code}).")

#HTTP status codes tell us what happened: 404 means "not found", 200 means "success". Any other code is treated as an unexpected error.

        data  = r.json()
        entry = data[0]
        ...
        for meaning in entry.get("meanings", []):
            ...
            for d in meaning.get("definitions", []):
                if d.get("definition"):
                    defs.append(d["definition"])

#The API returns a JSON list. The code digs through the nested structure to pull out definitions, examples, synonyms, and antonyms, then packages them into a `Word` object.



### Class: `QuizGenerator` — Creates Multiple-Choice Questions
class QuizGenerator:
    def __init__(self, saved_words):
        self.words = saved_words

    def generate_quiz(self, num_questions=5):
        if len(self.words) < 2:
            raise ValueError("Save at least 2 words to take a quiz.")
        pool = random.sample(self.words, min(num_questions, len(self.words)))
        questions = []
        for w in pool:
            correct = w.definitions[0] if w.definitions else "No definition"
            distractors = [x.definitions[0] for x in self.words
                           if x.word != w.word and x.definitions]
            random.shuffle(distractors)
            choices = distractors[:3] + [correct]
            random.shuffle(choices)
            questions.append({"word": w.word, "choices": choices, "answer": correct})
        return questions
#For each question it picks one word, takes its correct definition, then grabs 3 wrong definitions from other saved words as "distractors". 
#It shuffles everything so the correct answer isn't always in the same position. Returns a list of dictionaries, each with `word`, `choices`, and `answer`.

### Class: `SpacedRepetitionManager` — Smart Review Scheduler

class SpacedRepetitionManager:
    INTERVALS = [1, 3, 7, 14, 30]

#These are the review intervals in days. The idea: if you know a word well, you don't need to review it tomorrow — maybe in a week, then two weeks, then a month.
    def record_review(self, word, knew_it):
        rec = self._data.get(word, {"interval_idx": 0, "streak": 0})
        if knew_it:
            rec["streak"] += 1
            rec["interval_idx"] = min(rec["interval_idx"] + 1, len(self.INTERVALS) - 1)
        else:
            rec["streak"] = 0
            rec["interval_idx"] = 0
        days = self.INTERVALS[rec["interval_idx"]]
        rec["next_review"] = (date.today() + timedelta(days=days)).isoformat()
#When you mark a card as "I knew it", the interval index moves up (longer gap before next review).
#When you say "Still learning", it resets back to 1 day. `timedelta(days=days)` calculates the future date, saved as a string like `"2026-06-20"`.


    def due_today(self, words):
        today = date.today().isoformat()
        return [w for w in words if self._data.get(w, {}).get("next_review", today) <= today]

#This checks which words are due: any word whose `next_review` date is today or earlier (or has never been reviewed) gets added to the list.

### File Utility Functions

def _read(path):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return []

def _write(path, data):
    path.write_text(json.dumps(data, indent=2))

#Two simple helpers: `_read` safely loads a JSON file (returns empty list if file doesn't exist or is corrupted), `_write` saves data to a JSON file with nice indentation.
def load_saved_words():
    return [Word.from_dict(d) for d in _read(WORDS_FILE)]

def save_word(word):
    words = load_saved_words()
    if any(w.word == word.word for w in words):
        return   # don't save duplicates
    words.append(word)
    _write(WORDS_FILE, [w.to_dict() for w in words])

#`load_saved_words` reads the JSON file and turns each dictionary back into a `Word` object. `save_word` loads the existing list, checks for duplicates, appends the new word, and saves everything back.


## 📁 `ai_helper.py` — Talks to Gemini AI

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

def get_ai_content(word, definition, api_key):
    prompt = f"""For the English word "{word}" (meaning: {definition}), return ONLY this JSON:
{{
  "simple_explanation": "...",
  "example_sentence": "...",
  "memory_trick": "..."
}}
No markdown, no extra text."""

#The prompt is written very specifically — it tells Gemini exactly what format to respond in (pure JSON, nothing else). 
#This makes parsing the response much easier.


    r = requests.post(
        GEMINI_URL, params={"key": api_key},
        json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=20
    )
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    text = re.sub(r"```(?:json)?|```", "", text).strip()
    return json.loads(text)

#It sends a POST request with the prompt, then digs through the nested response to get the text. The `re.sub` line strips out any markdown code fences (` ```json `) that Gemini sometimes adds even when told not to. Finally `json.loads` converts the text into a Python dictionary.

## 📁 `app.py` — The User Interface
#This file controls everything the user sees and clicks on. It uses **Streamlit**, which turns Python code into a web app automatically.

### Setup
st.set_page_config(page_title="VocabVault", page_icon="📖", layout="centered")
```
#Sets the browser tab title and icon.

for k, v in {
    "word": None, "ai": None,
    "quiz_qs": [], "quiz_idx": 0, ...
}.items():
    if k not in st.session_state:
        st.session_state[k] = v
#Streamlit re-runs the entire script from top to bottom every time the user clicks anything. 
#`st.session_state` is a dictionary that persists between those re-runs — it's how the app remembers things like "which flashcard are we on?" or "what are the current quiz questions?". This loop sets default values only on the very first run.
### Sidebar

with st.sidebar:
    page = st.radio("", ["🔍 Search", "📚 My Words", ...])
    st.session_state.gemini_key = st.text_input("Gemini API Key", type="password", ...)

#The sidebar shows navigation (radio buttons) and the API key input. `type="password"` hides the key as dots. The selected page name drives the `if/elif` blocks below.

### Search Page

col1, col2 = st.columns([4, 1])
raw = col1.text_input(...)
go  = col2.button("Search", type="primary")

if go and raw.strip():
    with st.spinner("Looking up…"):
        try:
            word_obj = DictionaryClient().lookup(raw)
            st.session_state.word = word_obj
        except (ValueError, LookupError, ConnectionError, ...) as e:
            st.error(str(e))
            st.stop()

#Creates a two-column layout: wide text box + narrow button. When Search is clicked, it creates a `DictionaryClient`, calls `lookup()`, and stores the result in session state. All errors are caught and shown as red error messages. `st.stop()` halts the rest of the page from rendering if there's an error.

### Quiz Page
#The quiz has three states managed by session state variables:

#1. **Setup** (`quiz_qs` is empty) — shows the slider and Start button
#2. **Active** (`quiz_qs` has questions, `quiz_done` is False) — shows one question at a time; clicking any answer button moves to the next question and triggers a `st.rerun()`
#3. **Done** (`quiz_done` is True) — shows final score and answer review

    
for i, choice in enumerate(q["choices"]):
    if st.button(choice, key=f"q{idx}c{i}", use_container_width=True):
        correct = choice == q["answer"]
        st.session_state.quiz_answers[q["word"]] = {...}
        if correct:
            st.session_state.quiz_score += 1
        st.session_state.quiz_idx += 1
        ...
        st.rerun()

#Each choice is its own button. The `key` must be unique (hence `q{idx}c{i}`). When clicked, it records the answer, increments the score if correct, advances the index, and re-runs the app to show the next question.

### SRS Review Page
#Works similarly to the quiz but simpler — one card at a time, two buttons (Knew it / Still learning), each calling `srs.record_review()` which updates the next review date in the JSON file.

### Flashcard Page
#Uses `st.session_state.fc_idx` to track which card is showing, and `st.session_state.fc_show` (True/False) to track whether the answer is revealed. Each navigation button updates these values and calls `st.rerun()`.



## How It All Connects


#User types a word
   #   ↓
#app.py calls DictionaryClient().lookup(word)       ← models.py
   #   ↓
#DictionaryClient calls the Free Dictionary API     ← internet
   #   ↓
#Returns a Word object, stored in session_state
 #     ↓
#User clicks "Save Word"
   #   ↓
#app.py calls save_word(word_obj)                   ← models.py
    #  ↓
#Word is written to saved_words.json                ← data/
  #    ↓
#User clicks "Get AI Insights"
 #     ↓
#app.py calls get_ai_content(word, definition, key) ← ai_helper.py
 #     ↓
#Gemini API returns explanation + memory trick      ← internet
 #     ↓
#User takes a Quiz
#     ↓
#QuizGenerator(load_saved_words()).generate_quiz()  ← models.py
 #     ↓
#Score saved via save_quiz_score()                  ← data/

#Every piece has one clear responsibility — `models.py` handles data and logic, `ai_helper.py` handles Gemini, 
#and `app.py` handles what the user sees. That separation is what makes the code readable and easy to change later.
