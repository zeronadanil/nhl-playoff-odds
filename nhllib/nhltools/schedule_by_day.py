import argparse
from datetime import datetime

from nhlpy import NHLClient


def usage():
    print("USAGE: nhl schedule-by-day YYYY-MM-DD")
    print("Example:")
    print(" nhl schedule-by-day 2026-04-03")


def validate_date(date_string):
    try:
        datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError:
        raise ValueError("date must be in YYYY-MM-DD format")


def format_local_time(utc_string):
    start_utc = datetime.fromisoformat(utc_string.replace("Z", "+00:00"))
    start_local = start_utc.astimezone()
    return start_local.strftime("%b. %d, %Y %I:%M %p").replace(". 0", ". ")


def fetch_schedule_by_day(game_date):
    client = NHLClient()
    schedule = client.schedule.daily_schedule(date=game_date)
    return schedule.get("games", [])


def format_game(game):
    away = game["awayTeam"]["abbrev"]
    home = game["homeTeam"]["abbrev"]
    start = format_local_time(game["startTimeUTC"])
    state = game.get("gameState", "")
    return f"{away} @ {home} {start} [{state}]"


def format_schedule_by_day(game_date, games):
    lines = [f"NHL schedule for {game_date}:"]

    if not games:
        lines.append("No games found.")
        return "\n".join(lines)

    for game in games:
        lines.append(format_game(game))

    return "\n".join(lines)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="nhl schedule-by-day",
        description="Print NHL schedule for a given date.",
    )
    parser.add_argument("date", help="Date in YYYY-MM-DD format")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    try:
        validate_date(args.date)
    except ValueError:
        usage()
        raise SystemExit(1)

    games = fetch_schedule_by_day(args.date)
    print(format_schedule_by_day(args.date, games))


if __name__ == "__main__":
    main()
