from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, Enum, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base

class PlayingRole(str, enum.Enum):
    BATSMAN = "batsman"
    BOWLER = "bowler"
    ALLROUNDER = "allrounder"
    WICKETKEEPER = "wicketkeeper"

class BattingStyle(str, enum.Enum):
    RIGHT = "right"
    LEFT = "left"

class MatchFormat(str, enum.Enum):
    ROUND_ROBIN = "round_robin"
    KNOCKOUT = "knockout"

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    owner = Column(String)
    budget = Column(Float, default=100000.0)  # Total fixed budget

    players = relationship("Player", back_populates="team")

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    phone = Column(String, unique=True, index=True)
    age = Column(Integer)
    role = Column(Enum(PlayingRole))
    batting_style = Column(Enum(BattingStyle))
    fee_paid = Column(Boolean, default=False)
    base_price = Column(Float, default=1000.0)
    auction_price = Column(Float, nullable=True)
    is_sold = Column(Boolean, default=False)

    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    team = relationship("Team", back_populates="players")

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    team1_id = Column(Integer, ForeignKey("teams.id"))
    team2_id = Column(Integer, ForeignKey("teams.id"))
    match_format = Column(Enum(MatchFormat))
    scheduled_time = Column(DateTime, default=datetime.utcnow)
    is_completed = Column(Boolean, default=False)
    winner_id = Column(Integer, ForeignKey("teams.id"), nullable=True)

    team1 = relationship("Team", foreign_keys=[team1_id])
    team2 = relationship("Team", foreign_keys=[team2_id])
    winner = relationship("Team", foreign_keys=[winner_id])

class BallEvent(Base):
    __tablename__ = "ball_events"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    inning = Column(Integer)  # 1 or 2
    over = Column(Integer)
    ball = Column(Integer)

    bowler_id = Column(Integer, ForeignKey("players.id"))
    striker_id = Column(Integer, ForeignKey("players.id"))
    non_striker_id = Column(Integer, ForeignKey("players.id"))

    runs = Column(Integer, default=0)
    is_wide = Column(Boolean, default=False)
    is_no_ball = Column(Boolean, default=False)
    is_bye = Column(Boolean, default=False)
    is_leg_bye = Column(Boolean, default=False)
    is_wicket = Column(Boolean, default=False)
    wicket_type = Column(String, nullable=True) # e.g. bowled, caught, run out
    is_free_hit = Column(Boolean, default=False)

    match = relationship("Match")
    bowler = relationship("Player", foreign_keys=[bowler_id])
    striker = relationship("Player", foreign_keys=[striker_id])
    non_striker = relationship("Player", foreign_keys=[non_striker_id])
