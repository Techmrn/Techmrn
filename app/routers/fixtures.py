from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Match, Team, MatchFormat
from app.core.templates import templates
from itertools import combinations
import random

router = APIRouter(prefix="/fixtures", tags=["fixtures"])

@router.get("/", response_class=HTMLResponse)
async def get_fixtures(request: Request, db: Session = Depends(get_db)):
    matches = db.query(Match).all()
    teams = db.query(Team).all()
    return templates.TemplateResponse(request=request, name="fixtures.html", context={
        "matches": matches,
        "teams": teams
    })

@router.post("/generate")
async def generate_fixtures(
    request: Request,
    format: MatchFormat = Form(...),
    db: Session = Depends(get_db)
):
    teams = db.query(Team).all()
    if len(teams) < 2:
        matches = db.query(Match).all()
        return templates.TemplateResponse(request=request, name="fixtures.html", context={
            "matches": matches,
            "teams": teams,
            "error": "Need at least 2 teams to generate fixtures."
        })

    # Clear old fixtures
    db.query(Match).delete()
    db.commit()

    if format == MatchFormat.ROUND_ROBIN:
        matchups = list(combinations(teams, 2))
        for t1, t2 in matchups:
            match = Match(team1_id=t1.id, team2_id=t2.id, match_format=format)
            db.add(match)

    elif format == MatchFormat.KNOCKOUT:
        # Simplistic knockout generator (requires 2^n teams, padding randomly otherwise for a simple version)
        shuffled = teams[:]
        random.shuffle(shuffled)

        for i in range(0, len(shuffled) - 1, 2):
            match = Match(team1_id=shuffled[i].id, team2_id=shuffled[i+1].id, match_format=format)
            db.add(match)

    db.commit()

    matches = db.query(Match).all()
    return templates.TemplateResponse(request=request, name="fixtures.html", context={
        "matches": matches,
        "teams": teams,
        "success": f"{format.value.title()} fixtures generated successfully!"
    })
