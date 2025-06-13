import json
from sentence_transformers import SentenceTransformer
import re

print("Loading sentence transformer model...")
# Using a model that is good for semantic search and has a reasonable size
model = SentenceTransformer('Alibaba-NLP/gte-large-en-v1.5', trust_remote_code=True)
print("✅ Model loaded.")

def clean_text(text):
    """Removes HTML tags and extra whitespace from text."""
    return re.sub(r'<[^>]+>', '', text).strip().replace("\n", " ")

def create_forum_embeddings():
    """Loads forum data, generates embeddings for each post, and saves them."""
    print("\nProcessing forum data...")
    try:
        with open("my_tds_forum_data.json", "r", encoding="utf-8") as f:
            discourse_data = json.load(f)
        print(f"Loaded {len(discourse_data)} threads.")

        all_posts_text = []
        post_references = []

        for thread in discourse_data:
            for post in thread['posts']:
                # Combine title with post content for better context
                content_to_embed = thread['title'] + " " + clean_text(post['content'])
                if content_to_embed.strip(): # Ensure we don't process empty content
                    all_posts_text.append(content_to_embed)
                    post_references.append({
                        "url": thread['url'],
                        "text": thread['title']
                    })

        print(f"Generating embeddings for {len(all_posts_text)} posts. This may take a while...")
        embeddings = model.encode(all_posts_text, show_progress_bar=True)

        # Combine references with their embeddings
        output_data = []
        for i, ref in enumerate(post_references):
            output_data.append({
                "url": ref['url'],
                "text": ref['text'],
                "content": all_posts_text[i],
                "embedding": embeddings[i].tolist()
            })

        with open("forum_embeddings.json", "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)
        
        print("✅ Forum embeddings created and saved to forum_embeddings.json")

    except Exception as e:
        print(f"❌ Error processing forum data: {e}")


def create_book_embeddings():
    """Loads course book data, generates embeddings for each section, and saves them."""
    print("\nProcessing course book data...")
    try:
        with open("tds_book.json", "r", encoding="utf-8") as f:
            course_data = json.load(f)
        print(f"Loaded {len(course_data)} book sections.")

        all_sections_text = [clean_text(entry['content']) for entry in course_data]
        
        print(f"Generating embeddings for {len(all_sections_text)} book sections...")
        embeddings = model.encode(all_sections_text, show_progress_bar=True)
        
        # Combine original data with their embeddings
        output_data = []
        for i, entry in enumerate(course_data):
            output_data.append({
                "title": entry['title'],
                "filename": entry['filename'],
                "content": entry['content'], # Keep original content for snippets
                "embedding": embeddings[i].tolist()
            })

        with open("book_embeddings.json", "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)

        print("✅ Course book embeddings created and saved to book_embeddings.json")

    except Exception as e:
        print(f"❌ Error processing course book data: {e}")

if __name__ == "__main__":
    create_forum_embeddings()
    create_book_embeddings()
    print("\n🎉 All data processed and embeddings saved.")