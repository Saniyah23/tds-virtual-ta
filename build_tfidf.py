# build_tfidf.py
import json
import re
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def clean_text(text):
    """Removes HTML tags and extra whitespace."""
    if not text:
        return ""
    return re.sub(r'<[^>]+>', '', text).strip().replace("\n", " ")

def build_and_save_tfidf():
    """
    Loads all data, builds a TF-IDF model, and saves it for the API to use.
    """
    print("Building TF-IDF model. This may take a moment...")

    # --- 1. Load and prepare all documents ---
    all_docs = []
    doc_references = []

    # Load forum data
    with open("my_tds_forum_data.json", "r", encoding="utf-8") as f:
        discourse_data = json.load(f)
    for thread in discourse_data:
        full_text = clean_text(thread['title'] + " " + " ".join(p['content'] for p in thread['posts']))
        all_docs.append(full_text)
        doc_references.append({
            "type": "discourse",
            "title": thread['title'],
            "url": thread['url'],
            "content": full_text
        })

    # Load book data
    with open("tds_book.json", "r", encoding="utf-8") as f:
        course_data = json.load(f)
    for entry in course_data:
        content = clean_text(entry['content'])
        all_docs.append(content)
        doc_references.append({
            "type": "book",
            "title": entry['title'],
            "filename": entry['filename'],
            "content": content
        })
    
    print(f"Loaded a total of {len(all_docs)} documents.")

    # --- 2. Create and train the TF-IDF Vectorizer ---
    # We use stop_words='english' to ignore common English words like 'the', 'a', 'is'
    vectorizer = TfidfVectorizer(stop_words='english', lowercase=True)
    
    # This creates the matrix of TF-IDF features for all documents
    tfidf_matrix = vectorizer.fit_transform(all_docs)
    
    print("✅ TF-IDF model created.")

    # --- 3. Save the model and data for the API ---
    with open("tfidf_vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)
    
    with open("tfidf_matrix.pkl", "wb") as f:
        pickle.dump(tfidf_matrix, f)
        
    with open("doc_references.json", "w", encoding="utf-8") as f:
        json.dump(doc_references, f)

    print("✅ TF-IDF Vectorizer, Matrix, and References have been saved successfully!")

if __name__ == "__main__":
    build_and_save_tfidf()