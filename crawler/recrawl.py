import sqlite3
import datetime
import time

from crawler.crawl import (
    DB_PATH, HEADERS, fetch_page, extract_content,
    is_crawl_allowed, is_probably_html_page,
)

# Kitne purane pages re-crawl karein (days mein). None = sab pages.
RECRAWL_OLDER_THAN_DAYS = 7
MAX_PAGES_PER_RUN = 50  # ek baar mein zyada se zyada kitne re-crawl karein


def get_pages_to_recrawl(limit: int):
    """Sabse purane crawl hue pages nikalta hai (jo kabhi recrawl nahi hue, pehle wo)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cutoff = None
    if RECRAWL_OLDER_THAN_DAYS is not None:
        cutoff = (
            datetime.datetime.now() - datetime.timedelta(days=RECRAWL_OLDER_THAN_DAYS)
        ).isoformat()

    if cutoff:
        rows = conn.execute(
            """
            SELECT url FROM page_meta
            WHERE crawled_at < ?
            ORDER BY crawled_at ASC
            LIMIT ?
            """,
            (cutoff, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT url FROM page_meta ORDER BY crawled_at ASC LIMIT ?", (limit,)
        ).fetchall()

    conn.close()
    return [row["url"] for row in rows]


def update_page_meta(url: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO page_meta (url, crawled_at) VALUES (?, ?)",
        (url, datetime.datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def update_page_content(url: str, title: str, content: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE pages SET title = ?, content = ? WHERE url = ?",
        (title, content, url)
    )
    conn.commit()
    conn.close()


def get_stored_content(url: str) -> str:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT content FROM pages WHERE url = ?", (url,)).fetchone()
    conn.close()
    return row[0] if row else ""


def recrawl():
    urls = get_pages_to_recrawl(MAX_PAGES_PER_RUN)
    print(f"Re-crawling {len(urls)} pages (oldest first)...\n")

    updated = 0
    unchanged = 0
    failed = 0

    for url in urls:
        if not is_probably_html_page(url) or not is_crawl_allowed(url):
            print(f"Skipping: {url}")
            continue

        print(f"Checking: {url}")
        html = fetch_page(url)
        if not html:
            print("  -> Fetch failed, leaving as-is")
            failed += 1
            continue

        page_data = extract_content(html, url)
        if not page_data or len(page_data["content"]) < 100:
            print("  -> Extraction failed, leaving as-is")
            failed += 1
            continue

        old_content = get_stored_content(url)
        new_content = page_data["content"]

        if new_content.strip() != old_content.strip():
            update_page_content(url, page_data["title"], new_content)
            print("  -> Content changed, updated.")
            updated += 1
        else:
            print("  -> No change.")
            unchanged += 1

        update_page_meta(url)
        time.sleep(1.5)

    print(f"\nRe-crawl complete! Updated: {updated} / Unchanged: {unchanged} / Failed: {failed}")


if __name__ == "__main__":
    recrawl()