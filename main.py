from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, SQLModel, Field, create_engine, select
from typing import Optional

DATABASE_URL = "sqlite:///nba_finals.db"
engine = create_engine(DATABASE_URL)

app = FastAPI()


class Players(SQLModel, table=True):
    __tablename__ = "players"

    player_id: str = Field(primary_key=True)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    team: Optional[str] = None
    jersey_number: Optional[int] = None
    position: Optional[str] = None
    height: Optional[str] = None
    weight: Optional[int] = None
    birth_date: Optional[str] = None
    college: Optional[str] = None


class FinalsStats(SQLModel, table=True):
    __tablename__ = "finals_stats"

    player_id: str = Field(primary_key=True)
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


@app.get("/teams")
async def get_teams():
    with Session(engine) as session:
        teams = session.exec(
            select(Players.team).distinct().order_by(Players.team)
        ).all()
    return teams


@app.get("/roster")
async def get_roster(team: str):
    with Session(engine) as session:
        players = session.exec(
            select(
                Players.player_id,
                Players.first_name,
                Players.last_name,
                Players.jersey_number,
                Players.position
            )
            .where(Players.team == team)
            .order_by(Players.last_name, Players.first_name)
        ).all()

    return [
        {
            "player_id": pid,
            "first_name": first,
            "last_name": last,
            "jersey_number": jersey,
            "position": pos,
        }
        for pid, first, last, jersey, pos in players
    ]


@app.get("/player")
async def get_player(player_id: str):
    with Session(engine) as session:
        player = session.get(Players, player_id)
        if not player:
            return {"error": "Player not found"}

        stats = session.get(FinalsStats, player_id)

        bio = {
            "player_id": player.player_id,
            "first_name": player.first_name,
            "last_name": player.last_name,
            "team": player.team,
            "jersey_number": player.jersey_number,
            "position": player.position,
            "height": player.height,
            "weight": player.weight,
            "birth_date": player.birth_date,
            "college": player.college,
        }

        finals_stats = None
        if stats:
            finals_stats = {
                "games": stats.games,
                "ppg": stats.ppg,
                "rpg": stats.rpg,
                "apg": stats.apg,
                "fg_pct": stats.fg_pct,
                "three_pt_pct": stats.three_pt_pct,
                "ft_pct": stats.ft_pct,
                "turnovers": stats.turnovers,
                "steals": stats.steals,
                "blocks": stats.blocks,
                "fouls": stats.fouls,
            }

    return {"bio": bio, "finals_stats": finals_stats}


@app.get("/players_with_stats")
async def get_players_with_stats():
    with Session(engine) as session:
        rows = session.exec(
            select(Players, FinalsStats)
            .join(FinalsStats, Players.player_id == FinalsStats.player_id, isouter=True)
            .order_by(Players.team, Players.last_name)
        ).all()

    results = []
    for player, stats in rows:
        results.append(
            {
                "player_id": player.player_id,
                "games": stats.games if stats else 0,
                "first_name": player.first_name,
                "last_name": player.last_name,
                "team": player.team,
                "jersey_number": player.jersey_number,
                "position": player.position,
                "ppg": stats.ppg if stats else None,
                "rpg": stats.rpg if stats else None,
                "apg": stats.apg if stats else None,
                "fg_pct": stats.fg_pct if stats else None,
                "three_pt_pct": stats.three_pt_pct if stats else None,
                "ft_pct": stats.ft_pct if stats else None,
                "turnovers": stats.turnovers if stats else None,
                "steals": stats.steals if stats else None,
                "blocks": stats.blocks if stats else None,
                "fouls": stats.fouls if stats and stats.fouls is not None else 0,
            }
        )

    return results


app.mount("/", StaticFiles(directory="static", html=True), name="static")