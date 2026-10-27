import sqlite3
import time
import requests
import trafilatura

SEED_URLS = [
    # Python
    "https://docs.python.org/3/tutorial/index.html",
    "https://docs.python.org/3/tutorial/introduction.html",
    "https://docs.python.org/3/tutorial/controlflow.html",
    "https://realpython.com/python-first-steps/",
    "https://realpython.com/python-virtual-environments-a-primer/",
    "https://realpython.com/python-data-structures/",
    "https://www.freecodecamp.org/news/python-for-loops-explained/",
    "https://www.freecodecamp.org/news/python-list-comprehension/",
    "https://www.w3schools.com/python/python_functions.asp",
    "https://www.w3schools.com/python/python_dictionaries.asp",

    # JavaScript
    "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide",
    "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Functions",
    "https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Asynchronous",
    "https://www.freecodecamp.org/news/javascript-array-methods/",
    "https://www.freecodecamp.org/news/javascript-promises-explained/",
    "https://www.w3schools.com/js/js_arrow_function.asp",
    "https://www.w3schools.com/js/js_async.asp",

    # Web dev / HTML / CSS
    "https://developer.mozilla.org/en-US/docs/Web/HTML",
    "https://developer.mozilla.org/en-US/docs/Web/CSS",
    "https://www.freecodecamp.org/news/css-flexbox-explained/",
    "https://www.freecodecamp.org/news/css-grid-layout-guide/",

    # Git / GitHub
    "https://docs.github.com/en/get-started/quickstart/hello-world",
    "https://docs.github.com/en/get-started/using-git/about-git",
    "https://www.freecodecamp.org/news/git-basics/",

    # Linux basics
    "https://www.digitalocean.com/community/tutorials/how-to-install-python-3-and-set-up-a-programming-environment",
    "https://www.digitalocean.com/community/tutorials/linux-commands",
    "https://www.digitalocean.com/community/tutorial-collections/how-to-use-linux",

    # FastAPI / web backend
    "https://fastapi.tiangolo.com/tutorial/first-steps/",
    "https://fastapi.tiangolo.com/tutorial/path-params/",
    "https://realpython.com/fastapi-python-web-apis/",

    # SQL / databases
    "https://www.w3schools.com/sql/sql_intro.asp",
    "https://realpython.com/python-sql-libraries/",

    # General programming concepts
    "https://www.freecodecamp.org/news/what-is-an-api-in-english-please-b880a3214a82/",
    "https://www.freecodecamp.org/news/what-is-rest-api/",
    "https://www.freecodecamp.org/news/data-structures-for-beginners/",
    "https://www.freecodecamp.org/news/algorithmic-complexity-explained/",

        # Databases aur backend
    "https://www.digitalocean.com/community/tutorials/sqlite-vs-mysql-vs-postgresql-a-comparison-of-relational-database-management-systems",
    "https://www.freecodecamp.org/news/the-sql-handbook/",
    "https://www.mongodb.com/resources/products/fundamentals/crud",

    # DevOps / Cloud basics
    "https://www.freecodecamp.org/news/what-is-ci-cd/",
    "https://www.digitalocean.com/community/tutorials/an-introduction-to-ci-cd-best-practices",
    "https://www.freecodecamp.org/news/the-docker-handbook/",

    # Data structures & algorithms
    "https://www.freecodecamp.org/news/big-o-notation-why-it-matters-and-why-it-doesnt-1674cfa8a23c/",
    "https://www.freecodecamp.org/news/binary-search-algorithm/",
    "https://www.freecodecamp.org/news/how-sorting-algorithms-work/",
    "https://www.freecodecamp.org/news/linked-lists-explained/",

    # React / frontend frameworks
    "https://react.dev/learn",
    "https://react.dev/learn/thinking-in-react",
    "https://www.freecodecamp.org/news/react-hooks-fetch-data/",

    # Node.js
    "https://nodejs.org/en/learn/getting-started/introduction-to-nodejs",
    "https://www.freecodecamp.org/news/what-is-nodejs/",

    # Testing / software practices
    "https://www.freecodecamp.org/news/an-introduction-to-testing-in-python/",
    "https://realpython.com/python-testing/",

    # Machine Learning basics
    "https://www.freecodecamp.org/news/machine-learning-for-beginners/",
    "https://realpython.com/python-ai-neural-network/",

    # Linux / terminal
    "https://www.freecodecamp.org/news/the-linux-commands-handbook/",
    "https://www.digitalocean.com/community/tutorials/linux-permissions-basics-and-how-to-use-umask-on-a-vps",

    # Networking basics
    "https://www.freecodecamp.org/news/how-dns-works-explained-for-beginners/",
    "https://www.freecodecamp.org/news/what-is-an-http-request/",

    # Security basics
    "https://www.freecodecamp.org/news/web-security-fundamentals/",
    "https://owasp.org/www-project-top-ten/",
]

HEADERS = {
    "User-Agent": "PrivateSearchBot/0.1 (learning project; contact: your-email@example.com)"
}

DB_PATH = "search_index.db"


def setup_database():
    """Database aur table banata hai agar pehle se nahi hai."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS pages USING fts5(
            url, title, content
        )
    """)
    conn.commit()
    conn.close()


def fetch_page(url: str):
    """Ek URL ka raw HTML download karta hai."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"  -> Fetch fail: {url} ({e})")
        return None


def extract_content(html: str, url: str):
    """HTML se saaf text aur title nikalta hai."""
    extracted = trafilatura.extract(
        html, include_comments=False, include_tables=False,
        output_format="json", url=url
    )
    if not extracted:
        return None

    import json
    data = json.loads(extracted)
    return {
        "title": data.get("title") or url,
        "content": data.get("text") or "",
    }


def save_page(url: str, title: str, content: str):
    """Page ko database mein save karta hai."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO pages (url, title, content) VALUES (?, ?, ?)",
        (url, title, content)
    )
    conn.commit()
    conn.close()


def crawl():
    setup_database()
    print(f"Crawling {len(SEED_URLS)} URLs...\n")

    for url in SEED_URLS:
        print(f"Fetching: {url}")
        html = fetch_page(url)
        if not html:
            continue

        page_data = extract_content(html, url)
        if not page_data or len(page_data["content"]) < 100:
            print("  -> Skipped (content too short or empty)")
            continue

        save_page(url, page_data["title"], page_data["content"])
        print(f"  -> Saved: {page_data['title'][:60]}")

        time.sleep(1.5)

    print("\nCrawling complete!")


if __name__ == "__main__":
    crawl()