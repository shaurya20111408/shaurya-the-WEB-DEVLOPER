from app.ai_answer import generate_ai_answer
import sqlite3
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Private Search")
templates = Jinja2Templates(directory="templates")

DB_PATH = "search_index.db"


def run_search(q: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """
        SELECT url, title, snippet(pages, 2, '<b>', '</b>', '...', 20) AS snippet
        FROM pages
        WHERE pages MATCH ?
        ORDER BY rank
        LIMIT 10
        """,
        (q,)
    ).fetchall()

    conn.close()
    return [dict(row) for row in rows]


@app.get("/", response_class=HTMLResponse)
def home(request: Request, q: str = ""):
    results = []
    if q.strip():
        results = run_search(q)

    context = {
        "request": request,
        "query": q,
        "count": len(results),
        "results": results,
        "ai_answer": generate_ai_answer(q, results)
    }
    return templates.TemplateResponse(request=request, name="index.html", context=context)


@app.get("/search")
def search(q: str):
    if not q or len(q.strip()) == 0:
        return {"results": []}
    results = run_search(q)
    return {"query": q, "count": len(results), "results": results}