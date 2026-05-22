from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.core.templates import templates

app = FastAPI(title="Cricket Tournament Web Application")

# Mount static files (CSS, JS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

from app.routers import players, teams, auction, fixtures, scoring, stats

app.include_router(players.router)
app.include_router(teams.router)
app.include_router(auction.router)
app.include_router(fixtures.router)
app.include_router(scoring.router)
app.include_router(stats.router)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"title": "Home"})
