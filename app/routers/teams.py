from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Team
from app.core.templates import templates

router = APIRouter(prefix="/teams", tags=["teams"])

@router.get("/register", response_class=HTMLResponse)
async def get_register_team(request: Request):
    return templates.TemplateResponse(request=request, name="register_team.html")

@router.post("/register")
async def register_team(
    request: Request,
    name: str = Form(...),
    owner: str = Form(...),
    db: Session = Depends(get_db)
):
    existing_team = db.query(Team).filter(Team.name == name).first()
    if existing_team:
        return templates.TemplateResponse(request=request, name="register_team.html", context={"error": "Team name already taken."})

    new_team = Team(name=name, owner=owner)
    db.add(new_team)
    db.commit()
    db.refresh(new_team)

    return templates.TemplateResponse(request=request, name="register_team.html", context={"success": f"Team '{name}' registered successfully with budget 100,000!"})
