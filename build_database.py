import sqlite3
import json
import re
from sentence_transformers import SentenceTransformer
import numpy as np

def clean_text(text: str) -> str:
    """A simple function to clean text by removing HTML tags and extra whitespace."""
    if not text:
        return ""
    return re.sub(r'<[^>]+>', '', text).strip().replace("\n", " ")

def build_database():
    """
    Creates and populates a SQLite database with content and their embeddings
    from the course and discourse JSON files. This is an offline process that
    only needs to be run once.
    """
    # 1. Initialize the embedding model and the database connection
    print("Loading sentence-transformer model ('all-MiniLM-L6-v2')...")
    # Using a lightweight but effective model suitable for free-tier deployment
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅ Model loaded.")

    conn = sqlite3.connect("knowledge_base.db")
    cursor = conn.cursor()

    # 2. Create tables for discourse and course content
    cursor.execute('DROP TABLE IF EXISTS discourse_chunks')
    cursor.execute('DROP TABLE IF EXISTS course_chunks')
    cursor.execute('''
    CREATE TABLE discourse_chunks (
        id INTEGER PRIMARY KEY,
        topic_title TEXT,
        content TEXT,
        url TEXT,
        embedding BLOB
    )''')
    cursor.execute('''
    CREATE TABLE course_chunks (
        id INTEGER PRIMARY KEY,
        doc_title TEXT,
        content TEXT,
        original_url TEXT,
        embedding BLOB
    )''')
    print("✅ Database and tables created.")

    # 3. Process Discourse Data
    print("\nProcessing Discourse forum data...")
    with open("tds_discourse_cleaned.json", "r", encoding="utf-8") as f:
        discourse_data = json.load(f)

    discourse_texts_to_embed = [clean_text(item['text']) for item in discourse_data]
    
    print(f"Generating embeddings for {len(discourse_texts_to_embed)} discourse documents...")
    discourse_embeddings = model.encode(
        discourse_texts_to_embed,
        batch_size=32,  # Process in batches to manage memory
        show_progress_bar=True
    )

    for i, item in enumerate(discourse_data):
        embedding_bytes = discourse_embeddings[i].astype(np.float32).tobytes()
        cursor.execute("INSERT INTO discourse_chunks (topic_title, content, url, embedding) VALUES (?, ?, ?, ?)",
                       (item['topic_title'], item['text'], item['url'], embedding_bytes))
    print(f"✅ Inserted {len(discourse_data)} discourse embeddings into the database.")

    # 4. Process Course Book Data
    print("\nProcessing course book data...")
    with open("tds_course_cleaned.json", "r", encoding="utf-8") as f:
        course_data = json.load(f)

    course_texts_to_embed = [clean_text(entry['text']) for entry in course_data]

    print(f"Generating embeddings for {len(course_texts_to_embed)} book sections...")
    book_embeddings = model.encode(
        course_texts_to_embed,
        batch_size=32,
        show_progress_bar=True
    )

    for i, entry in enumerate(course_data):
        embedding_bytes = book_embeddings[i].astype(np.float32).tobytes()
        cursor.execute("INSERT INTO course_chunks (doc_title, content, original_url, embedding) VALUES (?, ?, ?, ?)",
                       (entry['filename'], entry['text'], entry['url'], embedding_bytes))
    print(f"✅ Inserted {len(course_data)} course book embeddings into the database.")

    # 5. Finalize
    conn.commit()
    conn.close()
    print("\n🎉 Database 'knowledge_base.db' has been built successfully!")

if __name__ == "__main__":
    build_database()