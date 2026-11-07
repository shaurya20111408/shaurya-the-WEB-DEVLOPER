import sqlite3
import time
import requests
import trafilatura
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

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

    # Cloud basics
    "https://docs.aws.amazon.com/whitepapers/latest/aws-overview/introduction.html",
    "https://learn.microsoft.com/en-us/azure/?product=popular",
    "https://cloud.google.com/docs/overview",

    # Mobile dev
    "https://developer.android.com/get-started/overview",
    "https://docs.flutter.dev/get-started/install",

    # DevOps / CI tools
    "https://docs.github.com/en/actions/writing-workflows/quickstart",
    "https://www.jenkins.io/doc/pipeline/tour/hello-world/",

    # Cybersecurity basics
    "https://owasp.org/www-project-web-security-testing-guide/",
    "https://developer.mozilla.org/en-US/docs/Web/Security",

    # General CS concepts
    "https://developer.mozilla.org/en-US/docs/Web/API",
    "https://developer.mozilla.org/en-US/docs/Learn/Common_questions/Web_mechanics/What_is_a_web_server",
    "https://www.w3schools.com/whatis/",

    # Package managers / build tools
    "https://docs.npmjs.com/about-npm",
    "https://pip.pypa.io/en/stable/getting-started/",

    # Shell / terminal
    "https://www.gnu.org/software/bash/manual/bash.html",

    # Markdown / documentation
    "https://www.markdownguide.org/getting-started/",
]

HEADERS = {
    "User-Agent": "PrivateSearchBot/0.1 (learning project; contact: your-email@example.com)"
}

DB_PATH = "search_index.db"

# Auto-expand settings
MAX_DEPTH = 1          # kitni "layers" andar links follow karein (0 = sirf seed, 1 = seed + unke links)
MAX_LINKS_PER_PAGE = 3  # har page se zyada se zyada kitne naye links follow karein


def setup_database():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS pages USING fts5(
            url, title, content
        )
    """)
    conn.commit()
    conn.close()


def fetch_page(url: str, max_retries: int = 3):
    """URL fetch karta hai, temporary failures par retry karta hai (exponential backoff ke saath)."""
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            # 404/403/401 jaisi errors retry karne se theek nahi hongi — turant give up
            if status in (404, 403, 401, 410):
                print(f"  -> Fetch fail (permanent, {status}): {url}")
                return None
            last_error = e
        except requests.RequestException as e:
            last_error = e

        if attempt < max_retries:
            wait_time = attempt * 2  # 2s, 4s, 6s...
            print(f"  -> Attempt {attempt} failed, retrying in {wait_time}s... ({url})")
            time.sleep(wait_time)

    print(f"  -> Fetch fail after {max_retries} attempts: {url} ({last_error})")
    return None


def extract_content(html: str, url: str):
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


def extract_links(html: str, base_url: str, same_domain_only: bool = True) -> list[str]:
    """Page ke andar se internal links nikalta hai (auto-expand ke liye)."""
    soup = BeautifulSoup(html, "html.parser")
    base_domain = urlparse(base_url).netloc

    links = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)

        if parsed.scheme not in ("http", "https"):
            continue
        if same_domain_only and parsed.netloc != base_domain:
            continue
        # fragments aur query junk clean karo
        clean_url = parsed._replace(fragment="", query="").geturl()
        links.append(clean_url)

    return links


def url_already_indexed(url: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT 1 FROM pages WHERE url = ? LIMIT 1", (url,)).fetchone()
    conn.close()
    return row is not None


def save_page(url: str, title: str, content: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO pages (url, title, content) VALUES (?, ?, ?)",
        (url, title, content)
    )
    conn.commit()
    conn.close()


def crawl_one(url: str, saved: list, failed: list) -> list[str]:
    """Ek URL crawl karta hai, save karta hai, aur uske andar ke links return karta hai."""
    print(f"Fetching: {url}")
    html = fetch_page(url)
    if not html:
        failed.append((url, "fetch failed"))
        return []

    page_data = extract_content(html, url)
    if not page_data:
        print("  -> Skipped (trafilatura could not extract anything)")
        failed.append((url, "extraction failed"))
        return []

    content_len = len(page_data["content"])
    if content_len < 100:
        print(f"  -> Skipped (content too short: {content_len} chars)")
        failed.append((url, f"content too short ({content_len} chars)"))
        return []

    save_page(url, page_data["title"], page_data["content"])
    print(f"  -> Saved: {page_data['title'][:60]}")
    saved.append(url)

    time.sleep(1.5)
    return extract_links(html, url)


def crawl():
    setup_database()
    print(f"Crawling {len(SEED_URLS)} seed URLs (auto-expand depth={MAX_DEPTH})...\n")

    saved = []
    failed = []
    visited = set(SEED_URLS)

    current_layer = list(SEED_URLS)

    for depth in range(MAX_DEPTH + 1):
        next_layer = []
        print(f"\n--- Depth {depth}: {len(current_layer)} URLs ---\n")

        for url in current_layer:
            if url_already_indexed(url):
                print(f"Skipping (already indexed): {url}")
                continue

            links = crawl_one(url, saved, failed)

            if depth < MAX_DEPTH:
                new_links = [l for l in links if l not in visited][:MAX_LINKS_PER_PAGE]
                for l in new_links:
                    visited.add(l)
                    next_layer.append(l)

        current_layer = next_layer

    print(f"\nCrawling complete! Saved: {len(saved)} / Failed: {len(failed)}\n")

    if failed:
        print("Failed URLs and reasons:")
        for url, reason in failed:
            print(f"  - {url}\n    Reason: {reason}")


if __name__ == "__main__":
    crawl()