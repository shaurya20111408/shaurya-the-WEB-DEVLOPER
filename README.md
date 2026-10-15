# Private Search Engine

Ek **privacy-first search engine**: koi tracking nahi, aur results ke upar AI ka chhota jawab (sources ke saath).

## Ek line mein
Koi cookie nahi, koi IP store nahi, koi search history nahi, aur AI jawab sources ke saath.

## Status
- [ ] Phase 1 — Tayyari (naam, niche, privacy rules, tools, repo)
- [ ] Phase 2 — Meta-search prototype (SearXNG + FastAPI + UI)
- [ ] Phase 3 — Privacy + deployment
- [ ] Phase 4 — Apna crawler + index
- [ ] Phase 5 — Ranking
- [ ] Phase 6 — AI answers
- [ ] Phase 7 — Polish + launch

## Tech stack (shuruat)
| Layer | Tool |
|---|---|
| Frontend | HTML + CSS + htmx |
| Backend | Python + FastAPI |
| Search | SearXNG → apna crawler + SQLite FTS5 |
| Server | Docker, Caddy (HTTPS) |

## Privacy
Dekho `PRIVACY.md`.