from pydantic import BaseModel
from typing import Optional
from app.models import PlayingRole, BattingStyle, MatchFormat

class PlayerCreate(BaseModel):
    name: str
    phone: str
    age: int
    role: PlayingRole
    batting_style: BattingStyle
    fee_paid: bool = False

class TeamCreate(BaseModel):
    name: str
    owner: str

class TeamResponse(TeamCreate):
    id: int
    budget: float

    class Config:
        orm_mode = True

class PlayerResponse(PlayerCreate):
    id: int
    base_price: float
    auction_price: Optional[float]
    is_sold: bool
    team_id: Optional[int]

    class Config:
        orm_mode = True
