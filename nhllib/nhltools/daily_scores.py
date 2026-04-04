import argparse
from datetime import datetime

from nhlpy import NHLClient


def usage():
    print("USAGE: nhl scores YYYY-MM-DD")
    print("Example:")
    print(" nhl scores 2026-04-03")


def format_local_time(utc_string):
    start_utc = datetime.fromisoformat(utc_string.replace("Z", "+00:00"))
    start_local = start_utc.astimezone()
    return start_local.strftime("%b. %d, %Y %I:%M %p").replace(". 0", ". ")


def fetch_daily_scores(game_date):
    client = NHLClient()
    scores = client.game_center.daily_scores(date=game_date)
    return scores.get("games", [])


def format_game(game):
    away = game["awayTeam"]["abbrev"]
    home = game["homeTeam"]["abbrev"]
    away_score = game["awayTeam"].get("score", 0)
    home_score = game["homeTeam"].get("score", 0)
    state = game.get("gameState", "")
    start = format_local_time(game["startTimeUTC"])
    return f"{away} {away_score} @ {home} {home_score} {start} [{state}]"


def format_results(game_date, games):
    lines = [f"NHL results for {game_date}:"]

    if not games:
        lines.append("No games found.")
        return "\n".join(lines)

    for game in games:
        lines.append(format_game(game))

    return "\n".join(lines)


def validate_date(game_date):
    try:
        datetime.strptime(game_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("date must be in YYYY-MM-DD format")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="nhl scores",
        description="Print NHL scores for a given date.",
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

    games = fetch_daily_scores(args.date)
    print(format_results(args.date, games))


if __name__ == "__main__":
    main()
