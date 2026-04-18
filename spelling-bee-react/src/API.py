from flask import Flask, request
from flask_restful import Api, Resource
from flask_cors import CORS
import pymysql, random, datetime, json
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)     # Create a Flask app instance
api = Api(app)            # Wrap it with Flask-RESTful to define API resources
CORS(app)                 # Enable CORS (Cross-Origin Resource Sharing)

# -------------------- DATABASE --------------------
def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        cursorclass=pymysql.cursors.DictCursor
    )

# -------------------- WORD CACHE --------------------
# A global set to store dictionary words in memory for O(1) lookup speed
VALID_WORDS = set()

def load_words():
    # Connects to the database and populates the global VALID_WORDS set.
    # Filters for words with at least 4 characters.
    global VALID_WORDS
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Query only words that meet the minimum length requirement
            cursor.execute("SELECT word FROM valid_words WHERE LENGTH(word) >= 4")
            # Use a set comprehension for efficient storage and fast membership testing
            VALID_WORDS = {row['word'] for row in cursor.fetchall()}
    finally:
        # Ensure the database connection is closed even if an error occurs
        conn.close()

def is_valid_word(word):
    # Checks if the provided word exists in the dictionary set.
    return word in VALID_WORDS

# -------------------- GAME LOGIC --------------------
def is_pangram(word, letters):
    # Determines if a word uses every letter in the provided puzzle set.
    # Returns True if all 'letters' are present at least once in 'word'.
    return set(letters).issubset(set(word))

def is_word_possible(word, letters):
    # Checks if a word is composed ONLY of the letters provided in the set.
    # Since letters can be reused, we simply check if the word's characters are a subset.
    return set(word).issubset(set(letters))

def get_valid_combinations(letters):
    center = letters[0] 
    valid_words = []
    letters_set = set(letters)

    for word in VALID_WORDS:
        # Check if the word contains the required center letter
        # and if all letters in the word are part of the allowed letter set
        if center in word and set(word).issubset(letters_set):
            valid_words.append(word)

    return valid_words


# -------------------- DAILY LETTERS --------------------
today_letters_cache = {}

def get_today_letters():
    
    today = datetime.date.today() # used as a unique key per day

    # If we've already generated today's puzzle, return it from cache
    if today in today_letters_cache:
        return today_letters_cache[today]

    # Seed the random generator with today's date
    random.seed(today.isoformat())

    # Minimum requirements for puzzle
    MIN_WORDS = 25       # Require at least this many valid words
    MIN_SCORE = 40       # Require a minimum total achievable score 

    # Step 1: Find all pangrams in the dictionary
    # A pangram is a word that uses exactly 7 unique letters
    pangrams = [w for w in VALID_WORDS if len(set(w)) == 7] # VALID_WORDS was populated when API.py was first ran

    # Track the best fallback puzzle in case none meet strict requirements
    best_letters = None
    best_score = 0

    # Step 2: Try multiple random pangrams to find a good puzzle
    for _ in range(200):
        # Pick a random pangram
        pangram = random.choice(pangrams)

        # Get random pangram's unique letters
        letters = list(set(pangram)) # ex:['t','r','i','a','n','g','l','e'] -> actually 7 unique

        # Returns a list of all valid words that can be made from these letters
        valid_words = get_valid_combinations(letters)

        # If no words can be formed, skip
        if not valid_words:
            continue

        # Calculate the total possible score for this puzzle
        score = calculate_score(valid_words, letters)

        # Only accept puzzles that have enough words and have can produce a good score
        if len(valid_words) >= MIN_WORDS and score >= MIN_SCORE:
            # Shuffle letters so they appear random to the user
            random.shuffle(letters)

            # Cache today's puzzle so future calls are instant
            today_letters_cache[today] = letters

            # Return (we have a good puzzle)
            return letters

        # If this puzzle isn't good enough, track it as a fallback
        # We keep the best scoring one in case none meet strict criteria
        if score > best_score:
            best_score = score
            best_letters = letters

    # Step 3: Fallback logic
    # If we couldn't find a "perfect" puzzle, use the best one we saw
    if best_letters:
        random.shuffle(best_letters)
        today_letters_cache[today] = best_letters
        return best_letters

    # If absolutely nothing worked
    raise Exception("Failed to generate puzzle")

# -------------------- SCORING --------------------
def calculate_score(words, letters):
    # Calculates the total score for a list of found words.
    
    # Scoring Rules:
    # - 4 letter words = 1 point.
    # - Words longer than 4 letters = points equal to their length.
    # - Pangram bonus = +7 points if the word uses every letter in the puzzle.
    
    # 1. Base Score: 1pt for length-4 words; length-pts for anything longer
    score = sum(1 if len(w) == 4 else len(w) for w in words)
    
    # 2. Bonus Points: Adds 7 points for every word that qualifies as a pangram
    score += sum(7 for w in words if is_pangram(w, letters))
    
    return score

def get_rank(score):
    if score >= 100:
        return "Genius"
    elif score >= 75:
        return "Amazing"
    elif score >= 50:
        return "Great"
    elif score >= 10:
        return "Good"
    return "Beginner"

# -------------------- SESSION HANDLING --------------------
def get_session(session_id):
    today = datetime.date.today()
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM user_stats WHERE session_id = %s AND date_played = %s",
                (session_id, today)
            )
            user = cursor.fetchone()

            if not user:
                cursor.execute(
                    "INSERT INTO user_stats (session_id, found_words, date_played) VALUES (%s, %s, %s)",
                    (session_id, json.dumps([]), today)
                )
                conn.commit()

                cursor.execute(
                    "SELECT * FROM user_stats WHERE session_id = %s AND date_played = %s",
                    (session_id, today)
                )
                user = cursor.fetchone()

        return user
    finally:
        conn.close()

def update_found_words(session_id, new_words):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE user_stats SET found_words = %s WHERE session_id = %s AND date_played = %s",
                (json.dumps(new_words), session_id, datetime.date.today())
            )
        conn.commit()
    finally:
        conn.close()

# -------------------- API RESOURCES --------------------
# ------------------- /api/game/today
class Game(Resource):
    def get(self):
        letters = get_today_letters()
        return {
            "status": "ok",
            "data": {
                "letters": letters,
                "center": letters[0]
            }
        }

api.add_resource(Game, '/api/game/today')
# --------------------

# -------------------- /api/check_word
class CheckWord(Resource):
    def post(self):
        data = request.get_json()

        word = data.get("word", "").lower()
        session_id = data.get("session_id")

        if not session_id:
            return {"status": "fail", "reason": "sesson error please reload and restart"}, 400

        if len(word) < 4:
            return {"status": "fail", "reason": "too short"}

        letters = get_today_letters()
        center = letters[0]

        # missing center
        if center not in word:
            return {"status": "fail", "reason": "missing center"}

        # invalid letters
        if not is_word_possible(word, letters):
            return {"status": "fail", "reason": "invalid letters"}

        # not in dictionary
        if not is_valid_word(word):
            return {"status": "fail", "reason": "not in dictionary"}

        # word is correct
        session = get_session(session_id)
        found_words = json.loads(session["found_words"])

        # already found
        if word in found_words:
            return {"status": "fail", "reason": "already found"}

        # update session's info
        found_words.append(word)
        update_found_words(session_id, found_words)

        score = calculate_score(found_words, letters)
        rank = get_rank(score)

        response = {
            "status": "ok",
            "data": {
                "total_points": score,
                "rank": rank
            }
        }

        # pangram
        if is_pangram(word, letters):
            response["data"]["pangram"] = True

        '''
        example successfull responce
        {
          "status": "ok",
          "data": {
              "total_points": 14,
              "rank": "Good Start",
              "pangram": true
          }
        }

        '''
        return response

api.add_resource(CheckWord, '/api/check_word')
# --------------------

# -------------------- /api/found_words
class GetFoundWords(Resource):
    def get(self):
        session_id = request.args.get("session_id")

        # clean page for new user
        if not session_id:
            return {
                "status": "ok",
                "data": {
                    "found_words": [],
                    "total_points": 0,
                    "rank": "Beginner"
                }
            }

        session = get_session(session_id)
        # words session has found so far
        found_words = json.loads(session["found_words"])
        letters = get_today_letters()

        score = calculate_score(found_words, letters)
        rank = get_rank(score)

        return {
            "status": "ok",
            "data": {
                "found_words": found_words,
                "total_points": score,
                "rank": rank
            }
        }
    
api.add_resource(GetFoundWords, '/api/found_words')
# --------------------

# -------------------- /api/restart
class RestartGame(Resource):
    def post(self):
        data = request.get_json()
        session_id = data.get("session_id")

        if not session_id:
            return {"status": "error", "message": "missing session_id"}, 400

        update_found_words(session_id, [])

        return {"status": "ok", "message": "restarted"}

api.add_resource(RestartGame, '/api/restart')
# --------------------

if __name__ == '__main__':
    load_words()  # preload dictionary into memory
    app.run(threaded=True, debug=True, port=5000)