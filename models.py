from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, create_engine

DATABASE_URL = "sqlite:///nba_finals.db"
engine = create_engine(DATABASE_URL)


class Players(SQLModel, table=True):
    __tablename__ = "players"

    player_id: str = Field(primary_key=True)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    jersey_number: Optional[int] = None
    position: Optional[str] = None
    height: Optional[str] = None
    weight: Optional[int] = None
    birth_date: Optional[str] = None
    college: Optional[str] = None

    finals_stats: Optional["FinalsStats"] = Relationship(back_populates="player")


class FinalsStats(SQLModel, table=True):
    __tablename__ = "finals_stats"

    player_id: str = Field(primary_key=True, foreign_key="players.player_id")
    team: Optional[str] = None
    games: Optional[int] = None
    ppg: Optional[float] = None
    rpg: Optional[float] = None
    apg: Optional[float] = None
    fg_pct: Optional[float] = None
    three_pt_pct: Optional[float] = None
    ft_pct: Optional[float] = None
    turnovers: Optional[float] = None
    steals: Optional[float] = None
    blocks: Optional[float] = None
    fouls: Optional[float] = None

    player: Optional[Players] = Relationship(back_populates="finals_stats")