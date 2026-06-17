import streamlit as st
import requests
import json
import random
import re
from datetime import datetime, timedelta
from pathlib import Path

# ==========================
# Custom Exceptions
# ==========================


class WordNotFoundError(Exception):
    pass


# ==========================
# Word Class
# ==========================

class Word:
    def __init__(self, word, definition,
                 phonetic="", examples=None,
                 synonyms=None, antonyms=None):

        self.word = word
        self.definition = definition
        self.phonetic = phonetic
        self.examples = examples or []
        self.synonyms = synonyms or []
        self.antonyms = antonyms or []


# ==========================
# Dictionary API Client
# ==========================

class DictionaryClient:

    BASE_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/"

    def get_word(self, word):

        url = self.BASE_URL + word

        try:
            response = requests.get(url)

            if response.status_code != 200:
                raise WordNotFoundError("Word not found")

            data = response.json()[0]

            definition = data["meanings"][0]["definitions"][0]["definition"]

            phonetic = ""

            if data.get("phonetics"):
                phonetic = data["phonetics"][0].get("text", "")

            examples = []
            synonyms = []
            antonyms = []

            for meaning in data["meanings"]:

                synonyms.extend(meaning.get("synonyms", []))
                antonyms.extend(meaning.get("antonyms", []))

                for d in meaning["definitions"]:
                    if d.get("example"):
                        examples.append(d["example"])

            return Word(
                word,
                definition,
                phonetic,
                examples,
                synonyms,
                antonyms
            )

        except requests.RequestException:
            raise Exception("API Connection Error")


# ==========================
# Flashcard Class
# ==========================

class Flashcard:

    FILE = "flashcards.json"

    def __init__(self, word, meaning):
        self.word = word
        self.meaning = meaning

    def save(self):

        cards = []

        try:
            with open(self.FILE, "r") as file:
                cards = json.load(file)

        except:
            cards = []

        cards.append({
            "word": self.word,
            "meaning": self.meaning
        })

        with open(self.FILE, "w") as file:
            json.dump(cards, file, indent=4)


# ==========================
# Quiz Generator
# ==========================

class QuizGenerator:

    def generate(self, word_obj):

        correct = word_obj.definition

        options = [
            correct,
            "A type of animal",
            "A country",
            "A vehicle"
        ]

        random.shuffle(options)

        return {
            "question":
            f"What is the meaning of '{word_obj.word}'?",
            "options": options,
            "answer": correct
        }


# ==========================
# Spaced Repetition Manager
# ==========================

class SpacedRepetitionManager:

    FILE = "reviews.json"

    intervals = [1, 3, 7, 14, 30]

    def schedule(self, word, level=0):

        review_date = (
            datetime.now()
            + timedelta(days=self.intervals[min(level, 4)])
        )

        data = {}

        try:
            with open(self.FILE, "r") as file:
                data = json.load(file)
        except:
            pass

        data[word] = review_date.strftime("%Y-%m-%d")

        with open(self.FILE, "w") as file:
            json.dump(data, file, indent=4)


# ==========================
# Utility Functions
# ==========================

SAVED_WORDS = "saved_words.json"
QUIZ_SCORES = "quiz_scores.json"


def save_word(word):

    words = []

    try:
        with open(SAVED_WORDS, "r") as file:
            words = json.load(file)
    except:
        pass

    if word not in words:
        words.append(word)

    with open(SAVED_WORDS, "w") as file:
        json.dump(words, file, indent=4)


def save_score(score):

    scores = []

    try:
        with open(QUIZ_SCORES, "r") as file:
            scores = json.load(file)
    except:
        pass

    scores.append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "score": score
    })

    with open(QUIZ_SCORES, "w") as file:
        json.dump(scores, file, indent=4)


# ==========================
# AI Functions
# (Placeholder without Gemini)
# ==========================

def simple_explanation(word):

    return (
        f"{word.word} simply means "
        f"{word.definition.lower()}."
    )


def memory_trick(word):

    return (
        f"Remember '{word.word}' "
        f"by connecting it to its meaning."
    )


# ==========================
# Streamlit UI
# ==========================

st.title("📚 Vocabulary Learning App")

user_word = st.text_input(
    "Enter a word"
)

if st.button("Search"):

    try:

        if not user_word.strip():
            raise ValueError("Input cannot be empty")

        if not re.match(r"^[A-Za-z]+$", user_word):
            raise ValueError(
                "Only letters are allowed"
            )

        dictionary = DictionaryClient()

        word = dictionary.get_word(
            user_word.lower()
        )

        st.subheader(word.word)

        st.write("Definition:")
        st.write(word.definition)

        st.write("Phonetic:")
        st.write(word.phonetic)

        st.write("Examples:")
        for e in word.examples[:3]:
            clean = re.sub(
                r"[^\w\s]",
                "",
                e
            )
            st.write("-", clean)

        st.write("Synonyms:")
        st.write(
            ", ".join(word.synonyms[:10])
        )

        st.write("Antonyms:")
        st.write(
            ", ".join(word.antonyms[:10])
        )

        st.subheader(
            "AI Simple Explanation"
        )
        st.write(
            simple_explanation(word)
        )

        st.subheader("Memory Trick")
        st.write(
            memory_trick(word)
        )

        if st.button("Save Word"):
            save_word(word.word)
            st.success(
                "Word saved."
            )

        if st.button(
            "Generate Flashcard"
        ):

            card = Flashcard(
                word.word,
                word.definition
            )

            card.save()

            srs = (
                SpacedRepetitionManager()
            )

            srs.schedule(word.word)

            st.success(
                "Flashcard saved."
            )

        quiz = QuizGenerator().generate(
            word
        )

        st.subheader("Quiz")

        answer = st.radio(
            quiz["question"],
            quiz["options"]
        )

        if st.button("Submit Quiz"):

            if answer == quiz["answer"]:

                st.success(
                    "Correct!"
                )

                save_score(1)

            else:

                st.error(
                    "Wrong Answer"
                )

                save_score(0)

    except Exception as e:
        st.error(str(e))


st.sidebar.title("Saved Words")

try:

    with open(
        SAVED_WORDS,
        "r"
    ) as file:

        words = json.load(file)

        for w in words:
            st.sidebar.write("•", w)

except:
    pass
