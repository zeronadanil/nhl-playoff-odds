#!/usr/bin/env python3

import argparse
import sys
from datetime import datetime
from nhlpy import NHLClient


def format_local_time(utc_string):
    start_utc = datetime.fromisoformat(utc_string.replace("Z", "+00:00"))
    start_local = start_utc.astimezone()
    return start_local.strftime("%b. %d, %Y %I:%M %p").replace(". 0", ". ")


def print_remaining_games(season, team_abbr):
    client = NHLClient()
    schedule = client.schedule.team_season_schedule(
        team_abbr=team_abbr.upper(),
        season=str(season)
    )

    now = datetime.now().astimezone()
    games = schedule.get("games", [])

    print(f"Remaining games for {team_abbr.upper()} in {season}:")

    found = False

    for game in games:
        start_utc = datetime.fromisoformat(game["startTimeUTC"].replace("Z", "+00:00"))
        start_local = start_utc.astimezone()

        if start_local >= now:
            away = game["awayTeam"]["abbrev"]
            home = game["homeTeam"]["abbrev"]
            when = format_local_time(game["startTimeUTC"])
            print(f"{away} @ {home}  {when}")
            found = True

    if not found:
        print("No remaining games found.")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Print remaining games for an NHL team in a given season."
    )
    parser.add_argument(
        "season",
        help="Season in YYYYYYYY format, for example 20252026"
    )
    parser.add_argument(
        "team",
        help="Three-letter team abbreviation, for example OTT"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if len(args.season) != 8 or not args.season.isdigit():
        print("Error: season must be in YYYYYYYY format, for example 20252026")
        sys.exit(1)

    if len(args.team) != 3 or not args.team.isalpha():
        print("Error: team must be a three-letter abbreviation, for example OTT")
        sys.exit(1)

    print_remaining_games(args.season, args.team)


if __name__ == "__main__":
    main()
