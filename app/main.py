import csv
import io
import sqlite3
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from app.ai_answer import generate_ai_answer
from app.stats import get_index_stats, check_system_health

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
    ai_answer = ""
    ai_sources = []

    if q.strip():
        results = run_search(q)
        if results:
            ai_answer = generate_ai_answer(q, results)
            ai_sources = results[:5]

    context = {
        "request": request,
        "query": q,
        "count": len(results),
        "results": results,
        "ai_answer": ai_answer,
        "ai_sources": ai_sources,
    }
    return templates.TemplateResponse(request=request, name="index.html", context=context)


@app.get("/search")
def search(q: str):
    if not q or len(q.strip()) == 0:
        return {"results": []}
    results = run_search(q)
    return {"query": q, "count": len(results), "results": results}


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    stats = get_index_stats()
    health = check_system_health()
    return templates.TemplateResponse(
        request=request, name="dashboard.html",
        context={"request": request, "stats": stats, "health": health}
    )


@app.get("/dashboard/export.csv")
def export_csv():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT url, title FROM pages").fetchall()
    conn.close()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["URL", "Title"])
    writer.writerows(rows)
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=index_export.csv"},
    )