# app.py (TF-IDF Version)
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import json
import re
import pickle
from fastapi.middleware.cors import CORSMiddleware
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

app = FastAPI(
    title="TDS Virtual TA (TF-IDF Edition)",
    description="Ask questions about the Tools in Data Science course.",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global variables for the TF-IDF model and data ---
vectorizer = None
tfidf_matrix = None
doc_references = []

@app.on_event("startup")
def load_model():
    """Load the TF-IDF model and references at startup."""
    global vectorizer, tfidf_matrix, doc_references
    try:
        with open("tfidf_vectorizer.pkl", "rb") as f:
            vectorizer = pickle.load(f)
        with open("tfidf_matrix.pkl", "rb") as f:
            tfidf_matrix = pickle.load(f)
        with open("doc_references.json", "r", encoding="utf-8") as f:
            doc_references = json.load(f)
        print("✅ TF-IDF model and data loaded successfully.")
    except Exception as e:
        print(f"❌ Error loading TF-IDF model: {e}")

# --- Pydantic Models ---
class QuestionRequest(BaseModel):
    question: str
    image: Optional[str] = None

class LinkItem(BaseModel):
    url: str
    text: str

class AnswerResponse(BaseModel):
    answer: str
    links: List[LinkItem]

# --- Helper Function ---
def clean_text(text):
    return re.sub(r'<[^>]+>', '', text).strip().replace("\n", " ")

# --- API Endpoint ---
@app.get("/")
def health_check():
    return {"status": "TDS Virtual TA API is live"}

@app.post("/api", response_model=AnswerResponse)
def answer_question(req: QuestionRequest):
    if not vectorizer:
        raise HTTPException(status_code=503, detail="Model is not loaded.")

    question = req.question

    # 1. Transform the user's question into a TF-IDF vector
    question_vector = vectorizer.transform([question])

    # 2. Compute cosine similarity between the question and all documents
    cosine_similarities = cosine_similarity(question_vector, tfidf_matrix).flatten()

    # 3. Get the indices of the top N most similar documents
    top_k = 5 # Get top 5 results to ensure good context
    # argsort returns indices that would sort the array, we take the last top_k in reverse
    top_indices = cosine_similarities.argsort()[-top_k:][::-1]

    # 4. Prepare the response
    answer_parts = []
    links = []
    seen_urls = set()

    for i in top_indices:
        doc = doc_references[i]
        
        # Construct URL based on document type
        if doc['type'] == 'discourse':
            url = doc['url']
        else: # 'book'
            url = f"https://github.com/sanand0/tools-in-data-science-public/blob/tds-2025-01/{doc['filename']}"

        if url not in seen_urls:
            title = doc['title']
            snippet = doc['content'].split(". ")[0] # Get the first sentence as a snippet
            
            answer_parts.append(f"{len(answer_parts) + 1}. {snippet} – [{title}]({url})")
            links.append({"url": url, "text": title})
            seen_urls.add(url)

    if not answer_parts:
        return AnswerResponse(answer="Sorry, I couldn't find any relevant answers.", links=[])

    return AnswerResponse(
        answer="\n".join(answer_parts),
        links=links
    )