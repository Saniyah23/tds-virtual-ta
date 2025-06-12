from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import json
import re
from pathlib import Path
from fastapi.responses import RedirectResponse

# Load Discourse data
with open("my_tds_forum_data.json", "r", encoding="utf-8") as f:
    discourse_data = json.load(f)

# Load Course Content
with open("tds_book.json", "r", encoding="utf-8") as f:
    course_data = json.load(f)

app = FastAPI(
    title="TDS Virtual TA",
    description="Ask questions about the Tools in Data Science course.",
    version="1.0.0",
    docs_url="/docs",          # 👈 Explicitly enable Swagger docs
    redoc_url="/redoc",        # 👈 Optional: ReDoc alternative docs
    openapi_url="/openapi.json"  # 👈 Also expose OpenAPI schema
)


# Redirect root to Swagger UI
@app.get("/")
def redirect_to_docs():
    return RedirectResponse(url="/docs")

class QuestionRequest(BaseModel):
    question: str

class LinkItem(BaseModel):
    url: str
    text: str

class AnswerResponse(BaseModel):
    answer: str
    links: List[LinkItem]

def clean_text(text):
    return re.sub(r'<[^>]+>', '', text).strip().replace("\n", " ")

def keyword_match(question, text):
    question_words = set(re.findall(r"\w+", question.lower()))
    text_words = set(re.findall(r"\w+", text.lower()))
    return len(question_words & text_words)

def find_best_threads(question: str, top_k: int = 3):
    results = []
    for thread in discourse_data:
        all_text = thread["title"] + " ".join(p["content"] for p in thread["posts"])
        score = keyword_match(question, all_text)
        if score > 0:
            results.append((score, thread))
    results.sort(reverse=True, key=lambda x: x[0])
    return [t for _, t in results[:top_k]]

def find_best_course_sections(question: str, top_k: int = 2):
    results = []
    for entry in course_data:
        score = keyword_match(question, entry["content"])
        if score > 3:
            results.append((score, entry))
    results.sort(reverse=True, key=lambda x: x[0])
    return [e for _, e in results[:top_k]]

@app.post("/api", response_model=AnswerResponse)
def answer_question(req: QuestionRequest):
    question = req.question
    threads = find_best_threads(question)
    notes = find_best_course_sections(question)

    answer_parts = []
    links = []

    # Discourse answers
    for idx, thread in enumerate(threads, 1):
        title = thread["title"]
        url = thread["url"]
        first_post = clean_text(thread["posts"][0]["content"])
        snippet = first_post.split(". ")[0]
        answer_parts.append(f"{idx}. {snippet} – [{title}]({url})")
        links.append({"url": url, "text": title})

    # Course content answers
    for note in notes:
        filename = note["filename"]
        title = note["title"]
        snippet = clean_text(note["content"].split("\n")[0])[:180]
        url = f"https://github.com/sanand0/tools-in-data-science-public/blob/tds-2025-01/{filename}"
        answer_parts.append(f"- From course notes: *{title}* – [{snippet}...]({url})")
        links.append({"url": url, "text": title})

    if not answer_parts:
        return AnswerResponse(answer="Sorry, I couldn't find any relevant answers.", links=[])

    return AnswerResponse(
        answer="\n".join(answer_parts),
        links=links
    )

# Run app with uvicorn for Spaces
import uvicorn
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=7860)
