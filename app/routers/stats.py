from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Match, Team, Player, BallEvent
from app.core.templates import templates

router = APIRouter(prefix="/stats", tags=["stats"])

@router.get("/points", response_class=HTMLResponse)
async def point_table(request: Request, db: Session = Depends(get_db)):
    teams = db.query(Team).all()
    standings = []

    for team in teams:
        # Calculate wins (matches where winner_id == team.id)
        wins = db.query(func.count(Match.id)).filter(Match.winner_id == team.id).scalar() or 0
        # Calculate losses (matches where team participated but did not win and is_completed is True)
        losses = db.query(func.count(Match.id)).filter(
            ((Match.team1_id == team.id) | (Match.team2_id == team.id)),
            Match.is_completed == True,
            Match.winner_id != team.id,
            Match.winner_id != None
        ).scalar() or 0

        # Simple points logic: 2 for a win, 0 for loss
        points = wins * 2

        standings.append({
            "name": team.name,
            "played": wins + losses,
            "wins": wins,
            "losses": losses,
            "points": points
        })

    standings.sort(key=lambda x: x["points"], reverse=True)

    return templates.TemplateResponse(request=request, name="points.html", context={
        "standings": standings
    })

@router.get("/leaderboards", response_class=HTMLResponse)
async def leaderboards(request: Request, db: Session = Depends(get_db)):
    # Top Run Scorers
    top_batsmen = db.query(
        Player.name,
        func.sum(BallEvent.runs).label('total_runs')
    ).join(BallEvent, Player.id == BallEvent.striker_id)\
     .group_by(Player.id)\
     .order_by(func.sum(BallEvent.runs).desc())\
     .limit(10).all()

    # Top Wicket Takers
    top_bowlers = db.query(
        Player.name,
        func.count(BallEvent.id).label('total_wickets')
    ).join(BallEvent, Player.id == BallEvent.bowler_id)\
     .filter(BallEvent.is_wicket == True)\
     .group_by(Player.id)\
     .order_by(func.count(BallEvent.id).desc())\
     .limit(10).all()

    return templates.TemplateResponse(request=request, name="leaderboards.html", context={
        "top_batsmen": top_batsmen,
        "top_bowlers": top_bowlers
    })
