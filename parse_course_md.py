import os
import json

COURSE_DIR = "tds_course_content"
OUTPUT_FILE = "tds_book.json"

def read_course_md():
    data = []
    for filename in sorted(os.listdir(COURSE_DIR)):
        if filename.endswith(".md") and not filename.startswith("_"):
            path = os.path.join(COURSE_DIR, filename)
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
                data.append({
                    "title": filename.replace(".md", "").replace("-", " ").title(),
                    "filename": filename,
                    "content": text
                })
    return data

def main():
    parsed = read_course_md()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {len(parsed)} course pages to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
