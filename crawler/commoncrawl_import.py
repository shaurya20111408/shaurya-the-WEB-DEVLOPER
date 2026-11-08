import io
import json
import time
import requests
from warcio.archiveiterator import ArchiveIterator

from crawler.crawl import setup_database, extract_content, save_page, url_already_indexed

HEADERS = {
    "User-Agent": "PrivateSearchBot/0.1 (learning project; contact: your-email@example.com)"
}

# Domains/paths ke patterns jinke liye Common Crawl se extra pages chahiye
QUERIES = [
    {"url": "en.wikipedia.org/wiki/India", "matchType": "exact"},
    {"url": "nationalgeographic.com", "matchType": "domain"},
    {"url": "bbc.com/news", "matchType": "prefix"},
]

MAX_RECORDS_PER_QUERY = 5


def get_latest_crawl_id() -> str:
    """Common Crawl ka sabse latest crawl collection ID dynamically fetch karta hai."""
    resp = requests.get(
        "https://index.commoncrawl.org/collinfo.json", headers=HEADERS, timeout=15
    )
    resp.raise_for_status()
    collections = resp.json()
    return collections[0]["id"]  # pehla entry hamesha sabse latest hota hai


def search_cc_index(crawl_id: str, query: dict, limit: int = 5):
    """Common Crawl ke index mein ek URL/pattern dhundta hai (retry ke saath, kyunki ye API kabhi-kabhi busy hota hai)."""
    index_url = f"https://index.commoncrawl.org/{crawl_id}-index"

    for attempt in range(1, 4):
        try:
            resp = requests.get(
                index_url,
                params={
                    "url": query["url"],
                    "matchType": query["matchType"],
                    "output": "json",
                    "limit": limit,
                },
                headers=HEADERS,
                timeout=20,
            )
            resp.raise_for_status()
            break
        except requests.RequestException as e:
            if attempt < 3:
                print(f"  -> Attempt {attempt} failed ({e}), retrying in 5s...")
                time.sleep(5)
            else:
                print(f"  -> Index query failed for {query['url']} after 3 attempts: {e}")
                return []

    records = []
    for line in resp.text.strip().split("\n"):
        if line:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def fetch_warc_html(record: dict):
    """Common Crawl ke storage se ek page ka raw HTML nikalta hai (byte-range request se)."""
    try:
        filename = record["filename"]
        offset = int(record["offset"])
        length = int(record["length"])
        warc_url = f"https://data.commoncrawl.org/{filename}"
        byte_range = f"bytes={offset}-{offset + length - 1}"

        resp = requests.get(
            warc_url, headers={**HEADERS, "Range": byte_range}, timeout=20
        )
        resp.raise_for_status()

        stream = io.BytesIO(resp.content)
        for warc_record in ArchiveIterator(stream):
            if warc_record.rec_type == "response":
                content = warc_record.content_stream().read()
                return content.decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  -> WARC fetch failed: {e}")
    return None


def import_from_common_crawl():
    setup_database()

    print("Fetching latest Common Crawl collection ID...")
    crawl_id = get_latest_crawl_id()
    print(f"Using crawl: {crawl_id}\n")

    saved = 0
    failed = 0

    for query in QUERIES:
        print(f"Searching Common Crawl for: {query['url']} ({query['matchType']})")
        records = search_cc_index(crawl_id, query, limit=MAX_RECORDS_PER_QUERY)
        print(f"  Found {len(records)} records")

        for record in records:
            url = record.get("url")
            if not url or url_already_indexed(url):
                continue

            print(f"Fetching from Common Crawl: {url}")
            html = fetch_warc_html(record)
            if not html:
                failed += 1
                continue

            page_data = extract_content(html, url)
            if not page_data or len(page_data["content"]) < 100:
                print("  -> Skipped (content too short or empty)")
                failed += 1
                continue

            save_page(url, page_data["title"], page_data["content"])
            print(f"  -> Saved: {page_data['title'][:60]}")
            saved += 1
            time.sleep(1)

        time.sleep(2)  # agli query se pehle thoda ruko, server ko overload mat karo

    print(f"\nCommon Crawl import complete! Saved: {saved} / Failed: {failed}")


if __name__ == "__main__":
    import_from_common_crawl()