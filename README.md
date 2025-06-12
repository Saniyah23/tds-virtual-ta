---
# Frontmatter for Hugging Face Spaces
sdk: docker
app_file: app.py
---

# TDS Virtual TA

A FastAPI-based assistant that answers student queries related to the "Tools in Data Science" course.

It uses two sources:
- **IITM Discourse forum data** (scraped manually and saved as `my_tds_forum_data.json`).
- **Official course notes** (parsed from markdown into `tds_book.json`).

## How to Use

Send a POST request to the `/api` endpoint with a JSON body:

```json
{
  "question": "How do I submit Assignment 2?"
}
```

The response will include:
- **`answer`**: A Markdown-formatted summary of relevant snippets.
- **`links`**: An array of objects with `url` and `text` fields referencing the forum thread or course note.

## Project Structure

```
├── app.py                 # FastAPI application
├── discourse.py           # Forum scraper (bonus script)
├── parse_course_md.py     # Markdown parser for course notes
├── requirements.txt       # Python dependencies
├── Dockerfile             # Container build recipe
├── my_tds_forum_data.json # Scraped Discourse data
├── tds_book.json          # Parsed course notes
├── tds_course_content/    # Raw markdown files (optional)
├── LICENSE                # MIT License
└── README.md              # This file
```

## Deployment on Hugging Face Spaces

This repository is configured to deploy on Hugging Face Spaces using Docker (port `7860`).

1. **Ensure files are at the repository root** (including `Dockerfile`, `app.py`, and `requirements.txt`).
2. **Push** to Hugging Face Space; frontmatter above instructs the platform to use Docker.
3. **Build** and **run** automatically; visit the URL below:

```
https://huggingface.co/spaces/<your-username>/tds-project-api
```

---

*Prepared by Saniyah Abdul Salam (23f300XXX).*
