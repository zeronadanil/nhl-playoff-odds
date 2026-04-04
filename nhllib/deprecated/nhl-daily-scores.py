#!/usr/bin/env python3

import argparse
import sys
from datetime import datetime
from nhlpy import NHLClient


def format_local_time(utc_string):
    start_utc = datetime.fromisoformat(utc_string.replace("Z", "+00:00"))
    start_local = start_utc.astimezone()
    return start_local.strftime("%b. %d, %Y %I:%M %p").replace(". 0", ". ")


def print_results(game_date):
    client = NHLClient()
    scores = client.game_center.daily_scores(date=game_date)
    games = scores.get("games", [])

    print(f"NHL results for {game_date}:")

    if not games:
        print("No games found.")
        return

    for game in games:
        away = game["awayTeam"]["abbrev"]
        home = game["homeTeam"]["abbrev"]
        away_score = game["awayTeam"].get("score", 0)
        home_score = game["homeTeam"].get("score", 0)
        state = game.get("gameState", "")
        start = format_local_time(game["startTimeUTC"])
        print(f"{away} {away_score} @ {home} {home_score}  {start}  [{state}]")


def parse_args():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("date", help="Date in YYYY-MM-DD format")
    return parser.parse_args()


def main():
    if len(sys.argv) < 2:
        print("USAGE: nhl-daily-scores yyyy-mm-dd")
        sys.exit(1)

    args = parse_args()

    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        print("USAGE: nhl-daily-scores yyyy-mm-dd")
        sys.exit(1)

    print_results(args.date)


if __name__ == "__main__":
    main()
