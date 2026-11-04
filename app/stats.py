import os
import sqlite3
from collections import Counter
from urllib.parse import urlparse

DB_PATH = "search_index.db"


def get_index_stats():
    """Index ke baare mein overview stats deta hai."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT url FROM pages").fetchall()
    conn.close()

    total_pages = len(rows)

    domain_counts = Counter()
    for (url,) in rows:
        domain = urlparse(url).netloc.replace("www.", "")
        domain_counts[domain] += 1

    top_domains = domain_counts.most_common(8)
    max_count = top_domains[0][1] if top_domains else 1

    chart_data = [
        {"domain": d, "count": c, "pct": round((c / max_count) * 100)}
        for d, c in top_domains
    ]

    last_crawl = None
    if os.path.exists(DB_PATH):
        mtime = os.path.getmtime(DB_PATH)
        import datetime
        last_crawl = datetime.datetime.fromtimestamp(mtime).strftime("%d %b %Y, %I:%M %p")

    return {
        "total_pages": total_pages,
        "total_sources": len(domain_counts),
        "last_crawl": last_crawl,
        "chart_data": chart_data,
    }


def check_system_health():
    """Server aur Ollama ka status check karta hai."""
    health = {"db_ok": False, "ollama_ok": False}

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("SELECT 1 FROM pages LIMIT 1")
        conn.close()
        health["db_ok"] = True
    except Exception:
        pass

    try:
        import requests
        resp = requests.get("http://localhost:11434", timeout=2)
        health["ollama_ok"] = resp.status_code == 200
    except Exception:
        pass

    return health