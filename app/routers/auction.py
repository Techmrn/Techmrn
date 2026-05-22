import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Player, Team
from app.core.templates import templates

router = APIRouter(prefix="/auction", tags=["auction"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.current_player_id: int | None = None
        self.current_bid: float = 0
        self.highest_bidder_id: int | None = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@router.get("/", response_class=HTMLResponse)
async def get_auction(request: Request, db: Session = Depends(get_db)):
    teams = db.query(Team).all()
    unsold_players = db.query(Player).filter(Player.is_sold == False).all()
    return templates.TemplateResponse(request=request, name="auction.html", context={
        "teams": teams,
        "unsold_players": unsold_players
    })

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, db: Session = Depends(get_db)):
    await manager.connect(websocket)
    try:
        # Send current state upon connection
        if manager.current_player_id:
            player = db.query(Player).filter(Player.id == manager.current_player_id).first()
            if player:
                await websocket.send_json({
                    "action": "current_state",
                    "player": {
                        "id": player.id,
                        "name": player.name,
                        "role": player.role,
                        "base_price": player.base_price
                    },
                    "current_bid": manager.current_bid,
                    "highest_bidder_id": manager.highest_bidder_id
                })

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            action = message.get("action")

            if action == "start_bidding" and client_id == "admin":
                player_id = message.get("player_id")
                player = db.query(Player).filter(Player.id == player_id, Player.is_sold == False).first()
                if player:
                    manager.current_player_id = player.id
                    manager.current_bid = player.base_price
                    manager.highest_bidder_id = None
                    await manager.broadcast({
                        "action": "new_player",
                        "player": {
                            "id": player.id,
                            "name": player.name,
                            "role": player.role,
                            "base_price": player.base_price
                        },
                        "current_bid": manager.current_bid
                    })

            elif action == "place_bid":
                team_id = int(message.get("team_id"))
                bid_amount = float(message.get("bid_amount"))

                if not manager.current_player_id:
                    continue

                team = db.query(Team).filter(Team.id == team_id).first()
                if not team or team.budget < bid_amount:
                    await websocket.send_json({"action": "error", "message": "Insufficient budget."})
                    continue

                if bid_amount > manager.current_bid:
                    manager.current_bid = bid_amount
                    manager.highest_bidder_id = team_id

                    await manager.broadcast({
                        "action": "bid_update",
                        "current_bid": manager.current_bid,
                        "highest_bidder_id": manager.highest_bidder_id,
                        "highest_bidder_name": team.name
                    })

            elif action == "sold" and client_id == "admin":
                if manager.current_player_id and manager.highest_bidder_id:
                    player = db.query(Player).filter(Player.id == manager.current_player_id).first()
                    team = db.query(Team).filter(Team.id == manager.highest_bidder_id).first()

                    if player and team and team.budget >= manager.current_bid:
                        player.is_sold = True
                        player.team_id = team.id
                        player.auction_price = manager.current_bid
                        team.budget -= manager.current_bid
                        db.commit()

                        await manager.broadcast({
                            "action": "player_sold",
                            "player_name": player.name,
                            "team_name": team.name,
                            "amount": manager.current_bid
                        })

                        manager.current_player_id = None
                        manager.current_bid = 0
                        manager.highest_bidder_id = None

    except WebSocketDisconnect:
        manager.disconnect(websocket)
