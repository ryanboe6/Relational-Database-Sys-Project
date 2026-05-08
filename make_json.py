import pandas as pd
import json

players = pd.read_csv("players.csv")
stats = pd.read_csv("finals_stats.csv")

data = players.merge(stats, on=["player_id", "team"], how="left")
data = data.fillna(0)

records = data.to_dict(orient="records")

with open("data.json", "w") as f:
    json.dump(records, f, indent=4)

print("data.json created successfully.")