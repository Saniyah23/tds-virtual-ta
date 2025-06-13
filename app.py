# app.py (Semantic Search Version)
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# --- Configuration and Initialization ---
app = FastAPI(
    title="TDS Virtual TA (Semantic Search)",
    description="Ask questions using semantic search.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global Models and Data (loaded into memory at startup) ---
model = None
all_embeddings = []
all_references = []
EMBEDDING_DIM = 384 # Dimension for 'all-MiniLM-L6-v2'

@app.on_event("startup")
def load_resources():
    """Load the model and pre-computed embeddings into memory at startup."""
    global model, all_embeddings, all_references
    
    print("Loading sentence-transformer model 'all-MiniLM-L6-v2'...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅ Model loaded.")

    print("Loading data from database...")
    try:
        conn = sqlite3.connect("knowledge_base.db", check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Load and combine all data and embeddings
        cursor.execute("SELECT topic_title as title, content, url, embedding FROM discourse_chunks")
        discourse_rows = cursor.fetchall()
        
        cursor.execute("SELECT doc_title as title, content, original_url as url, embedding FROM course_chunks")
        markdown_rows = cursor.fetchall()

        conn.close()

        # Combine and process data
        for row in discourse_rows + markdown_rows:
            all_references.append(dict(row))
            all_embeddings.append(np.frombuffer(row['embedding'], dtype=np.float32))

        # Convert to a single numpy matrix for efficient computation
        all_embeddings = np.array(all_embeddings).reshape(-1, EMBEDDING_DIM)
        print(f"✅ Loaded {len(all_references)} documents into memory.")

    except Exception as e:
        print(f"❌ Error loading data from database: {e}")

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

# --- API Endpoints ---
@app.get("/")
def health_check():
    return {"status": "TDS Virtual TA API is live"}

@app.post("/api", response_model=AnswerResponse)
def answer_question(req: QuestionRequest):
    if model is None or len(all_embeddings) == 0:
        raise HTTPException(status_code=503, detail="Model or data not loaded yet.")

    question = req.question

    # 1. Get embedding for the user's question
    question_embedding = model.encode([question])

    # 2. Compute cosine similarity between the question and all documents
    similarities = cosine_similarity(question_embedding, all_embeddings)[0]

    # 3. Get the indices of the top 5 most similar documents
    top_k = 5
    top_indices = np.argsort(similarities)[-top_k:][::-1]

    # 4. Prepare the response
    answer_parts = []
    links = []
    seen_urls = set()

    for i in top_indices:
        doc = all_references[i]
        url = doc['url']
        
        if url and url not in seen_urls:
            title = doc['title']
            # Get the first sentence of the content as a snippet
            snippet = doc['content'].split(". ")[0]
            
            answer_parts.append(f"{len(answer_parts) + 1}. {snippet} – [{title}]({url})")
            links.append({"url": url, "text": title})
            seen_urls.add(url)

    if not answer_parts:
        return AnswerResponse(answer="Sorry, I couldn't find any relevant answers.", links=[])

    return AnswerResponse(
        answer="\n".join(answer_parts),
        links=links
    )