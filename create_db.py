import pandas as pd
import sqlite3

DB_PATH = "nba_finals.db"

# Read CSVs
players = pd.read_csv("players.csv")
finals_stats = pd.read_csv("finals_stats.csv")

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cur = conn.cursor()

# --- coerce float columns that are really integers (whole numbers + NaN) ---
def coerce_float_to_int(df):
    for col in df.columns:
        if pd.api.types.is_float_dtype(df[col]):
            non_null = df[col].dropna()
            if len(non_null) > 0 and (non_null == non_null.astype(int)).all():
                df[col] = df[col].astype(pd.Int64Dtype())
    return df

players = coerce_float_to_int(players)
finals_stats = coerce_float_to_int(finals_stats)

# --- helper to map pandas dtypes to SQLite column types ---
def sqlite_type(dtype):
    if pd.api.types.is_integer_dtype(dtype):
        return "INTEGER"
    elif pd.api.types.is_float_dtype(dtype):
        return "REAL"
    else:
        return "TEXT"

# --- players table ---
cols = ", ".join(
    f'"{c}" {sqlite_type(players[c])}' for c in players.columns
)
cur.execute(f'CREATE TABLE players ({cols}, PRIMARY KEY ("player_id"))')

# --- finals_stats table ---
cols = ", ".join(
    f'"{c}" {sqlite_type(finals_stats[c])}' for c in finals_stats.columns
)
cur.execute(
    f"""CREATE TABLE finals_stats (
        {cols},
        PRIMARY KEY ("player_id"),
        FOREIGN KEY ("player_id") REFERENCES players ("player_id")
    )"""
)

# --- insert data ---
players.to_sql("players", conn, if_exists="append", index=False)
finals_stats.to_sql("finals_stats", conn, if_exists="append", index=False)

conn.commit()
conn.close()
print("nba_finals.db created successfully.")