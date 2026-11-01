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
    "https://www.freecodecamp.org/news/python-for-loop-example-and-tutorial/",
    "https://www.freecodecamp.org/news/list-comprehension-in-python/",
    "https://www.w3schools.com/python/python_functions.asp",
    "https://www.w3schools.com/python/python_dictionaries.asp",

    # JavaScript
    "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide",
    "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Functions",
    "https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Asynchronous",
    "https://www.freecodecamp.org/news/complete-introduction-to-the-most-useful-javascript-array-methods/",
    "https://www.freecodecamp.org/news/javascript-promises-explained/",
    "https://www.w3schools.com/js/js_arrow_function.asp",
    "https://www.w3schools.com/js/js_async.asp",

    # Web dev / HTML / CSS
    "https://developer.mozilla.org/en-US/docs/Web/HTML",
    "https://developer.mozilla.org/en-US/docs/Web/CSS",

    # Git / GitHub
    "https://docs.github.com/en/get-started/quickstart/hello-world",
    "https://docs.github.com/en/get-started/using-git/about-git",

    # Linux basics
    "https://www.digitalocean.com/community/tutorials/how-to-install-python-3-and-set-up-a-programming-environment",
    "https://www.digitalocean.com/community/tutorials/linux-commands",

    # FastAPI / web backend
    "https://fastapi.tiangolo.com/tutorial/first-steps/",
    "https://fastapi.tiangolo.com/tutorial/path-params/",
    "https://realpython.com/fastapi-python-web-apis/",

    # SQL / databases
    "https://www.w3schools.com/sql/sql_intro.asp",
    "https://realpython.com/python-sql-libraries/",

    # General programming concepts
    "https://www.freecodecamp.org/news/what-is-an-api-in-english-please-b880a3214a82/",

    # Databases aur backend
    "https://www.digitalocean.com/community/tutorials/sqlite-vs-mysql-vs-postgresql-a-comparison-of-relational-database-management-systems",
    "https://www.mongodb.com/resources/products/fundamentals/crud",

    # DevOps / Cloud basics
    "https://www.freecodecamp.org/news/what-is-ci-cd/",
    "https://www.digitalocean.com/community/tutorials/an-introduction-to-ci-cd-best-practices",
    "https://www.freecodecamp.org/news/the-docker-handbook/",

    # Data structures & algorithms
    "https://www.freecodecamp.org/news/big-o-notation-why-it-matters-and-why-it-doesnt-1674cfa8a23c/",

    # React / frontend frameworks
    "https://react.dev/learn",
    "https://react.dev/learn/thinking-in-react",

    # Node.js
    "https://nodejs.org/en/learn/getting-started/introduction-to-nodejs",

    # Testing / software practices
    "https://www.freecodecamp.org/news/an-introduction-to-testing-in-python/",
    "https://realpython.com/python-testing/",

    # Machine Learning basics
    "https://realpython.com/python-ai-neural-network/",

    # Linux / terminal
    "https://www.freecodecamp.org/news/the-linux-commands-handbook/",
    "https://www.digitalocean.com/community/tutorials/linux-permissions-basics-and-how-to-use-umask-on-a-vps",

    # Security basics
    "https://owasp.org/www-project-top-ten/",

        # TypeScript
    "https://www.typescriptlang.org/docs/handbook/intro.html",
    "https://www.typescriptlang.org/docs/handbook/2/basic-types.html",

    # Vue.js
    "https://vuejs.org/guide/introduction.html",
    "https://vuejs.org/guide/essentials/reactivity-fundamentals.html",

    # Django / Flask (Python web frameworks)
    "https://docs.djangoproject.com/en/5.1/intro/overview/",
    "https://flask.palletsprojects.com/en/stable/quickstart/",

    # Go
    "https://go.dev/doc/tutorial/getting-started",

    # Rust
    "https://doc.rust-lang.org/book/ch01-00-getting-started.html",

    # Docker / Kubernetes basics
    "https://docs.docker.com/get-started/docker-overview/",
    "https://kubernetes.io/docs/concepts/overview/",

    # GraphQL
    "https://graphql.org/learn/",

    # Redis
    "https://redis.io/docs/latest/develop/get-started/",

    # Data science: Pandas / NumPy
    "https://pandas.pydata.org/docs/getting_started/overview.html",
    "https://numpy.org/doc/stable/user/absolute_beginners.html",

    # Regex
    "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Regular_expressions",

    # Testing frameworks
    "https://docs.pytest.org/en/stable/getting-started.html",

    # API design
    "https://restfulapi.net/",
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

    saved = []
    failed = []

    for url in SEED_URLS:
        print(f"Fetching: {url}")
        html = fetch_page(url)
        if not html:
            failed.append((url, "fetch failed"))
            continue

        page_data = extract_content(html, url)
        if not page_data:
            print("  -> Skipped (trafilatura could not extract anything)")
            failed.append((url, "extraction failed"))
            continue

        content_len = len(page_data["content"])
        if content_len < 100:
            print(f"  -> Skipped (content too short: {content_len} chars)")
            failed.append((url, f"content too short ({content_len} chars)"))
            continue

        save_page(url, page_data["title"], page_data["content"])
        print(f"  -> Saved: {page_data['title'][:60]}")
        saved.append(url)

        time.sleep(1.5)

    print(f"\nCrawling complete! Saved: {len(saved)} / Failed: {len(failed)}\n")

    if failed:
        print("Failed URLs and reasons:")
        for url, reason in failed:
            print(f"  - {url}\n    Reason: {reason}")


if __name__ == "__main__":
    crawl()