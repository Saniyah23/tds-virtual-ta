from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Dict
import uvicorn
import json
import re
from pathlib import Path

# Load scraped data
with open("my_tds_forum_data.json", "r", encoding="utf-8") as f:
    discourse_data = json.load(f)

# Initialize FastAPI
app = FastAPI()

# Request format
class QuestionRequest(BaseModel):
    question: str

# Response format
class LinkItem(BaseModel):
    url: str
    text: str

class AnswerResponse(BaseModel):
    answer: str
    links: List[LinkItem]

# Basic keyword matcher
def find_best_threads(question: str, top_k: int = 3):
    question_words = set(re.findall(r"\w+", question.lower()))
    results = []

    for thread in discourse_data:
        all_text = thread["title"] + " ".join(p["content"] for p in thread["posts"])
        text_words = set(re.findall(r"\w+", all_text.lower()))
        score = len(question_words & text_words)
        if score > 0:
            results.append((score, thread))

    results.sort(reverse=True, key=lambda x: x[0])
    return [t for _, t in results[:top_k]]

@app.post("/api", response_model=AnswerResponse)
def answer_question(req: QuestionRequest):
    matched_threads = find_best_threads(req.question)

    if not matched_threads:
        return AnswerResponse(
            answer="Sorry, I couldn't find any relevant answers in the forum.",
            links=[]
        )

    answer_parts = []
    links = []

    for idx, thread in enumerate(matched_threads, 1):
        title = thread["title"]
        url = thread["url"]
        first_post = thread["posts"][0]["content"]
        cleaned = re.sub(r'<[^>]+>', '', first_post).strip().replace("\n", " ")
        truncated = cleaned.split(". ")[0]  # Take first sentence only
        answer_parts.append(f"{idx}. {truncated.strip()} – [{title}]({url})")
        links.append({"url": url, "text": title})

    full_answer = "\n".join(answer_parts)
    return AnswerResponse(answer=full_answer, links=links)

# Uncomment below to run locally
# if __name__ == "__main__":
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
