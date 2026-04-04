#!/usr/bin/env python3

import sys
from datetime import datetime
from nhlpy import NHLClient


def usage():
    print("USAGE: nhl-schedule-by-day.py YYYY-MM-DD")
    print("Example: nhl-schedule-by-day.py 2026-04-03")


def validate_date(date_string):
    try:
        datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def format_local_time(utc_string):
    start_utc = datetime.fromisoformat(utc_string.replace("Z", "+00:00"))
    start_local = start_utc.astimezone()
    return start_local.strftime("%b. %d, %Y %I:%M %p").replace(". 0", ". ")


def print_schedule_by_day(game_date):
    client = NHLClient()
    schedule = client.schedule.daily_schedule(date=game_date)
    games = schedule.get("games", [])

    print(f"NHL schedule for {game_date}:")

    if not games:
        print("No games found.")
        return

    for game in games:
        away = game["awayTeam"]["abbrev"]
        home = game["homeTeam"]["abbrev"]
        start = format_local_time(game["startTimeUTC"])
        state = game.get("gameState", "")
        print(f"{away} @ {home}  {start}  [{state}]")


def main():
    if len(sys.argv) != 2:
        usage()
        sys.exit(1)

    game_date = sys.argv[1]

    if not validate_date(game_date):
        usage()
        sys.exit(1)

    print_schedule_by_day(game_date)


if __name__ == "__main__":
    main()
