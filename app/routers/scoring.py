import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Match, Player, Team, BallEvent
from app.core.templates import templates

router = APIRouter(prefix="/scoring", tags=["scoring"])

class ScoreManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, match_id: int):
        await websocket.accept()
        if match_id not in self.active_connections:
            self.active_connections[match_id] = []
        self.active_connections[match_id].append(websocket)

    def disconnect(self, websocket: WebSocket, match_id: int):
        if match_id in self.active_connections:
            self.active_connections[match_id].remove(websocket)

    async def broadcast(self, match_id: int, message: dict):
        if match_id in self.active_connections:
            for connection in self.active_connections[match_id]:
                await connection.send_json(message)

manager = ScoreManager()

@router.get("/{match_id}", response_class=HTMLResponse)
async def get_scoring_panel(request: Request, match_id: int, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    team1_players = db.query(Player).filter(Player.team_id == match.team1_id).all()
    team2_players = db.query(Player).filter(Player.team_id == match.team2_id).all()

    return templates.TemplateResponse(request=request, name="scoring.html", context={
        "match": match,
        "team1_players": team1_players,
        "team2_players": team2_players
    })

@router.post("/{match_id}/ball")
async def log_ball(
    match_id: int,
    inning: int = Form(...),
    over: int = Form(...),
    ball: int = Form(...),
    bowler_id: int = Form(...),
    striker_id: int = Form(...),
    non_striker_id: int = Form(...),
    runs: int = Form(0),
    is_wide: bool = Form(False),
    is_no_ball: bool = Form(False),
    is_bye: bool = Form(False),
    is_leg_bye: bool = Form(False),
    is_wicket: bool = Form(False),
    wicket_type: str = Form(None),
    is_free_hit: bool = Form(False),
    db: Session = Depends(get_db)
):
    event = BallEvent(
        match_id=match_id,
        inning=inning,
        over=over,
        ball=ball,
        bowler_id=bowler_id,
        striker_id=striker_id,
        non_striker_id=non_striker_id,
        runs=runs,
        is_wide=is_wide,
        is_no_ball=is_no_ball,
        is_bye=is_bye,
        is_leg_bye=is_leg_bye,
        is_wicket=is_wicket,
        wicket_type=wicket_type,
        is_free_hit=is_free_hit
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    # Broadcast update
    await manager.broadcast(match_id, {
        "action": "ball_logged",
        "details": {
            "over": over,
            "ball": ball,
            "runs": runs,
            "extras": "Wide" if is_wide else "No Ball" if is_no_ball else "Bye" if is_bye else "Leg Bye" if is_leg_bye else "",
            "wicket": is_wicket
        }
    })

    return {"message": "Ball logged successfully"}

@router.post("/{match_id}/complete")
async def complete_match(
    match_id: int,
    winner_id: int = Form(...),
    db: Session = Depends(get_db)
):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    match.is_completed = True
    match.winner_id = winner_id
    db.commit()

    return {"message": "Match completed successfully"}

@router.websocket("/ws/{match_id}")
async def websocket_scoring(websocket: WebSocket, match_id: int):
    await manager.connect(websocket, match_id)
    try:
        while True:
            # We just keep connection open, client receives broadcast updates
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, match_id)
