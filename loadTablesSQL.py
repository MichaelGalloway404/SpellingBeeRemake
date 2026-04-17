import pymysql
from dotenv import load_dotenv
import os, sys

load_dotenv()

print("Starting script...")

if not os.path.isfile('words.txt'):
    print("Error: words.txt file not found.")
    sys.exit()

conn = None

try:
    conn = pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        cursorclass=pymysql.cursors.DictCursor
    )
    print("Connected to database!")
    cursor = conn.cursor()

    # print number of words added to DB
    inserted = 0

    with open('words.txt', 'r') as file:
        for line in file:
            word = line.strip().lower()
            print(f"Read word: '{word}'")
            if word:
                try:
                    cursor.execute("INSERT IGNORE INTO valid_words (word) VALUES (%s)", (word,))
                    if cursor.rowcount == 1: # 1 == inserted, and 0 == already existed aka 0 rows changed
                        inserted += 1
                        print(f"Inserted: '{word}'")
                    else:
                        print(f"Skipped duplicate or failed insert: '{word}'")
                except pymysql.MySQLError as e:
                    print(f"Error inserting {word}: {e}")

    conn.commit()
    print(f"Words loaded successfully. {inserted} words inserted.")

except pymysql.MySQLError as err:
    print(f"Error connecting to MySQL: {err}")

finally:
    if conn:
        try:
            cursor.close()
            conn.close()
            print("Connection closed.")
        except Exception as e:
            print(f"Error during cleanup: {e}")