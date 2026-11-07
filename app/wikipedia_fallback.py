import requests

HEADERS = {
    "User-Agent": "PrivateSearchBot/0.1 (learning project; contact: your-email@example.com)"
}


def search_wikipedia(query: str):
    """Wikipedia se live search karke top article ka summary deta hai."""
    try:
        # Step 1: Query se matching article dhundo
        search_resp = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": 1,
            },
            headers=HEADERS,
            timeout=6,
        )
        search_resp.raise_for_status()
        search_data = search_resp.json()
        results = search_data.get("query", {}).get("search", [])
        if not results:
            return None

        title = results[0]["title"]

        # Step 2: Us article ka summary nikalo
        summary_resp = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}",
            headers=HEADERS,
            timeout=6,
        )
        summary_resp.raise_for_status()
        summary_data = summary_resp.json()

        extract = summary_data.get("extract", "")
        page_url = summary_data.get("content_urls", {}).get("desktop", {}).get("page", "")

        if not extract or not page_url:
            return None

        return {
            "url": page_url,
            "title": f"{title} — Wikipedia",
            "snippet": extract[:300] + ("..." if len(extract) > 300 else ""),
        }
    except requests.RequestException:
        return None     