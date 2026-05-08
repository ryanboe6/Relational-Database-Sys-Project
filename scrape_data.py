import re
import pandas as pd


PACERS_URL = "pacers.html"
THUNDER_URL = "thunder.html"
FINALS_URL = "finals.html"


def fetch_tables(path: str) -> list[pd.DataFrame]:
    return pd.read_html(path)


def clean_name(name: str) -> str:
    if pd.isna(name):
        return ""
    name = str(name).strip()
    name = name.replace("*", "")
    return re.sub(r"\s+", " ", name)


def split_name(full_name: str) -> tuple[str, str]:
    parts = clean_name(full_name).split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return " ".join(parts[:-1]), parts[-1]


def make_player_id(full_name: str) -> str:
    full_name = clean_name(full_name)
    parts = full_name.split()
    if not parts:
        return ""
    last = re.sub(r"[^a-z]", "", parts[-1].lower())
    first_initial = re.sub(r"[^a-z]", "", parts[0].lower())[:1]
    return f"{last}_{first_initial}"


def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [
            " ".join(str(x).strip() for x in col if str(x) != "nan").strip()
            for col in df.columns
        ]
    else:
        df.columns = [str(c).strip() for c in df.columns]
    return df


def standardize_basic_stat_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = flatten_columns(df)

    rename_map = {}
    for col in df.columns:
        col_clean = str(col).strip()

        if col_clean.endswith("Player") or col_clean == "Player":
            rename_map[col] = "Player"
        elif col_clean.endswith("G") or col_clean == "G":
            rename_map[col] = "G"
        elif col_clean.endswith("FG%") or col_clean == "FG%":
            rename_map[col] = "FG%"
        elif col_clean.endswith("3P%") or col_clean == "3P%":
            rename_map[col] = "3P%"
        elif col_clean.endswith("FT%") or col_clean == "FT%":
            rename_map[col] = "FT%"
        elif col_clean.endswith("TRB") or col_clean == "TRB":
            rename_map[col] = "TRB"
        elif col_clean.endswith("AST") or col_clean == "AST":
            rename_map[col] = "AST"
        elif col_clean.endswith("PTS") or col_clean == "PTS":
            rename_map[col] = "PTS"
        elif col_clean.endswith("TOV") or col_clean == "TOV":
            rename_map[col] = "TOV"
        elif col_clean.endswith("STL") or col_clean == "STL":
            rename_map[col] = "STL"
        elif col_clean.endswith("BLK") or col_clean == "BLK":
            rename_map[col] = "BLK"
        elif col_clean.endswith("PF") or col_clean == "PF":
            rename_map[col] = "PF"

    df = df.rename(columns=rename_map)
    return df


def roster_table_from_page(path: str) -> pd.DataFrame:
    tables = fetch_tables(path)

    for df in tables:
        df = flatten_columns(df)
        cols = set(df.columns)
        if {"Player", "No.", "Pos", "Ht", "Wt", "Birth Date", "College"}.issubset(cols):
            return df.copy()

    raise ValueError(f"Could not find roster table in {path}")


def scrape_players(path: str, team_name: str) -> pd.DataFrame:
    roster = roster_table_from_page(path).copy()

    roster = roster[roster["Player"].notna()].copy()
    roster["Player"] = roster["Player"].apply(clean_name)
    roster = roster[roster["Player"] != "Player"].copy()

    roster["player_id"] = roster["Player"].apply(make_player_id)
    roster["first_name"] = roster["Player"].apply(lambda x: split_name(x)[0])
    roster["last_name"] = roster["Player"].apply(lambda x: split_name(x)[1])

    roster["jersey_number"] = pd.to_numeric(roster["No."], errors="coerce").astype("Int64")
    roster["position"] = roster["Pos"].astype(str).str.strip()
    roster["height"] = roster["Ht"].astype(str).str.strip()
    roster["weight"] = pd.to_numeric(roster["Wt"], errors="coerce").astype("Int64")
    roster["birth_date"] = roster["Birth Date"].astype(str).str.strip()
    roster["college"] = roster["College"].fillna("").astype(str).str.strip()

    players = roster[
        [
            "player_id",
            "first_name",
            "last_name",
            "jersey_number",
            "position",
            "height",
            "weight",
            "birth_date",
            "college",
        ]
    ].copy()

    players["team"] = team_name
    return players


def scrape_finals_stats(players_df: pd.DataFrame) -> pd.DataFrame:
    tables = fetch_tables(FINALS_URL)

    needed = {"Player", "G", "FG%", "3P%", "FT%", "TRB", "AST", "PTS", "TOV", "STL", "BLK", "PF"}
    matched_tables = []

    for df in tables:
        temp = standardize_basic_stat_columns(df)
        if needed.issubset(set(temp.columns)):
            matched_tables.append(temp)

    if len(matched_tables) == 0:
        raise ValueError("Could not find Finals player stats tables.")

    combined = pd.concat(matched_tables, ignore_index=True)
    combined = combined.loc[:, ~combined.columns.duplicated()].copy()

    combined["Player"] = combined["Player"].apply(clean_name)
    combined = combined[combined["Player"].notna()].copy()
    combined = combined[combined["Player"] != ""].copy()
    combined = combined[~combined["Player"].isin(["Team Totals", "Reserves", "Starters", "Player"])].copy()

    combined["player_id"] = combined["Player"].apply(make_player_id)

    numeric_cols = ["G", "TRB", "AST", "PTS", "TOV", "STL", "BLK", "PF", "FG%", "3P%", "FT%"]
    # remove duplicate column names, keep first copy
    combined = combined.loc[:, ~combined.columns.duplicated()].copy()

    for col in numeric_cols:
        if col in combined.columns:
            combined[col] = pd.to_numeric(combined[col], errors="coerce")

    combined = combined.dropna(subset=["G"]).copy()
    combined = combined[combined["G"] > 0].copy()
    combined = combined.drop_duplicates(subset=["player_id"]).copy()

    combined["games"] = combined["G"].astype("Int64")
    combined["ppg"] = (combined["PTS"] / combined["G"]).round(2)
    combined["rpg"] = (combined["TRB"] / combined["G"]).round(2)
    combined["apg"] = (combined["AST"] / combined["G"]).round(2)
    combined["turnovers"] = (combined["TOV"] / combined["G"]).round(2)
    combined["steals"] = (combined["STL"] / combined["G"]).round(2)
    combined["blocks"] = (combined["BLK"] / combined["G"]).round(2)
    combined["fouls"] = (combined["PF"] / combined["G"]).round(2)

    combined["fg_pct"] = combined["FG%"]
    combined["three_pt_pct"] = combined["3P%"]
    combined["ft_pct"] = combined["FT%"]

    combined = combined.merge(
        players_df[["player_id", "team"]],
        on="player_id",
        how="left"
    )

    finals_stats = combined[
        [
            "player_id",
            "team",
            "games",
            "ppg",
            "rpg",
            "apg",
            "fg_pct",
            "three_pt_pct",
            "ft_pct",
            "turnovers",
            "steals",
            "blocks",
            "fouls",
        ]
    ].copy()

    return finals_stats


def main() -> None:
    pacers_players = scrape_players(PACERS_URL, "Indiana Pacers")
    thunder_players = scrape_players(THUNDER_URL, "Oklahoma City Thunder")

    players = pd.concat([pacers_players, thunder_players], ignore_index=True)
    players = players.drop_duplicates(subset=["player_id"]).copy()

    finals_stats = scrape_finals_stats(players)

    players_output = players[
        [
            "player_id",
            "team",
            "first_name",
            "last_name",
            "jersey_number",
            "position",
            "height",
            "weight",
            "birth_date",
            "college",
        ]
    ].copy()

    players_output.to_csv("players.csv", index=False)
    finals_stats.to_csv("finals_stats.csv", index=False)

    print("Created players.csv and finals_stats.csv successfully.")


if __name__ == "__main__":
    main()