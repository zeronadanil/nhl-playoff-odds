import argparse
from datetime import datetime

from nhlpy import NHLClient


def usage():
    print("USAGE: nhl remaining-games YYYYYYYY TEAM")
    print("Examples:")
    print(" nhl remaining-games 20252026 OTT")
    print(" nhl remaining-games 20252026 TOR")


def format_local_time(utc_string):
    start_utc = datetime.fromisoformat(utc_string.replace("Z", "+00:00"))
    start_local = start_utc.astimezone()
    return start_local.strftime("%b. %d, %Y %I:%M %p").replace(". 0", ". ")


def fetch_team_schedule(season, team_abbr):
    client = NHLClient()
    schedule = client.schedule.team_season_schedule(
        team_abbr=team_abbr.upper(),
        season=str(season),
    )
    return schedule.get("games", [])


def get_remaining_games(season, team_abbr, now=None):
    if now is None:
        now = datetime.now().astimezone()

    games = fetch_team_schedule(season, team_abbr)
    remaining = []

    for game in games:
        start_utc = datetime.fromisoformat(game["startTimeUTC"].replace("Z", "+00:00"))
        start_local = start_utc.astimezone()
        if start_local >= now:
            remaining.append(game)

    return remaining


def format_game(game):
    away = game["awayTeam"]["abbrev"]
    home = game["homeTeam"]["abbrev"]
    when = format_local_time(game["startTimeUTC"])
    return f"{away} @ {home} {when}"


def format_remaining_games(season, team_abbr, games):
    lines = [f"Remaining games for {team_abbr.upper()} in {season}:"]

    if not games:
        lines.append("No remaining games found.")
        return "\n".join(lines)

    for game in games:
        lines.append(format_game(game))

    return "\n".join(lines)


def validate_inputs(season, team_abbr):
    if len(season) != 8 or not season.isdigit():
        raise ValueError("season must be in YYYYYYYY format, for example 20252026")

    if len(team_abbr) != 3 or not team_abbr.isalpha():
        raise ValueError("team must be a three-letter abbreviation, for example OTT")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="nhl remaining-games",
        description="Print remaining games for an NHL team in a given season.",
    )
    parser.add_argument(
        "season",
        help="Season in YYYYYYYY format, for example 20252026",
    )
    parser.add_argument(
        "team",
        help="Three-letter team abbreviation, for example OTT",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    try:
        validate_inputs(args.season, args.team)
    except ValueError as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)

    games = get_remaining_games(args.season, args.team)
    print(format_remaining_games(args.season, args.team, games))


if __name__ == "__main__":
    main()
