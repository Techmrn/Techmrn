from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Player, PlayingRole, BattingStyle
from app.core.templates import templates

router = APIRouter(prefix="/players", tags=["players"])

@router.get("/register", response_class=HTMLResponse)
async def get_register_player(request: Request):
    return templates.TemplateResponse(request=request, name="register_player.html")

@router.post("/register")
async def register_player(
    request: Request,
    name: str = Form(...),
    phone: str = Form(...),
    age: int = Form(...),
    role: PlayingRole = Form(...),
    batting_style: BattingStyle = Form(...),
    fee_paid: bool = Form(False),
    db: Session = Depends(get_db)
):
    # Check if player already exists
    existing_player = db.query(Player).filter(Player.phone == phone).first()
    if existing_player:
        return templates.TemplateResponse(request=request, name="register_player.html", context={"error": "Player with this phone number already registered."})

    new_player = Player(
        name=name,
        phone=phone,
        age=age,
        role=role,
        batting_style=batting_style,
        fee_paid=fee_paid
    )
    db.add(new_player)
    db.commit()
    db.refresh(new_player)

    return templates.TemplateResponse(request=request, name="register_player.html", context={"success": "Player registered successfully!"})
