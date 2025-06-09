import requests
import json
import time
from datetime import datetime

# --- CONFIGURATION ---
BASE_URL = "https://discourse.onlinedegree.iitm.ac.in"
CATEGORY_ID = 34  # TDS Knowledge Base Category ID
START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2025, 4, 14)

# 🔒 Replace this with your full cookie string from DevTools or document.cookie
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Cookie": "_forum_session=V6kCFtTL%2BuytH%2Far8ZKXC2hf8QpKqp%2FHI%2FXIKmmfaBE6K%2F1%2Fj7LyhrcJ4xrd5oCS%2F6T4bG6C4s5AFkK0lCxTPnZhjKgE9MvzjN1ZRvC1lA2bzFkEs5yWbae77ICiR%2FPK1sSlmInOFEyNTNhpM6AAtnfmxTAIEnlvf3rFxUyPv9lUOD82YClhFr1CRk7nMYgc%2BAQu3g%2Fp8KLnrRW0QdwLIX45d8SThqTbUS0MOxMHJ4BuoM0gzYyorN3Ms8N0u181JomO0kLltSzYIGPZy4SlHpR4gQzhnA%3D%3D--5E%2B9GfZ%2Fcx%2BQ%2FdWV--zCqG0R9Tb2FbtRLJKxtwRQ%3D%3D; _t=ga6NeFQwvyuMoujVEk7Ceu%2B0GrZ%2Fnuz4MYT%2FhfSEXNJaVxuQaPVmKjdQvjmPVFdt24dB4frsMI4lmE9EtaEQNVJtQK%2FHe3cxlGoR8%2FZJsHx3wG8Az%2F2msM4cJwNeefGqEXNiw2iAv4eVnKVa2sK9VsUQ4ZoqrnYuiSDsGos734P2q21jgejyCxhMg%2F%2FRsz0XPW7MZiJk8JTmT2kmLc74ETcTNmQoE2yd%2BuyHnpWiRZCFUitF0fGcJe%2B5NW1jv6B7RxCWwjwdTbflXIrtJrWwtT%2FCIwif1hCnQ5WWxh3MZAhMY2OfdnWYoaxaSDk%3D--ekW3ARAHXMJ90xj1--wp6aiBwvZ6%2F%2FsajoFJ26Cg%3D%3D"
}

# --- FUNCTIONS ---
def get_topics_in_category(page=0):
    url = f"{BASE_URL}/c/courses/tds-kb/{CATEGORY_ID}.json?page={page}"
    res = requests.get(url, headers=HEADERS)
    print(f"Page {page} Status: {res.status_code}")
    print("Response Preview:", res.text[:300])

    if res.status_code != 200:
        return []
    return res.json().get("topic_list", {}).get("topics", [])

def get_topic_details(slug, topic_id):
    url = f"{BASE_URL}/t/{slug}/{topic_id}.json"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        print(f"❌ Failed to fetch topic {topic_id}: {res.status_code}")
        return None
    return res.json()

def is_in_range(date_str):
    try:
        d = datetime.strptime(date_str[:10], "%Y-%m-%d")
        return START_DATE <= d <= END_DATE
    except:
        return False

# --- MAIN SCRAPER ---
def main():
    all_threads = []
    page = 0
    consecutive_empty_pages = 0
    MAX_EMPTY = 3

    while consecutive_empty_pages < MAX_EMPTY:
        topics = get_topics_in_category(page)
        if not topics:
            consecutive_empty_pages += 1
            page += 1
            continue

        consecutive_empty_pages = 0
        for topic in topics:
            created_at = topic.get("created_at", "")
            if not is_in_range(created_at):
                continue

            slug = topic.get("slug")
            topic_id = topic.get("id")
            print(f"✅ Fetching topic: {topic['title']}")

            topic_data = get_topic_details(slug, topic_id)
            if not topic_data:
                continue

            posts = [
                {
                    "username": p["username"],
                    "created_at": p["created_at"],
                    "content": p["cooked"]
                } for p in topic_data["post_stream"]["posts"]
            ]

            all_threads.append({
                "id": topic_id,
                "title": topic["title"],
                "url": f"{BASE_URL}/t/{slug}/{topic_id}",
                "created_at": created_at,
                "posts": posts
            })

            time.sleep(1)

        page += 1

    with open("my_tds_forum_data.json", "w", encoding="utf-8") as f:
        json.dump(all_threads, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(all_threads)} threads to my_tds_forum_data.json")

# --- RUN ---
if __name__ == "__main__":
    main()
