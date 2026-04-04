#!/usr/bin/env python3

import sys
from datetime import datetime
from nhlpy import NHLClient


FINAL_STATES = {"OFF", "FINAL"}
POSTPONED_STATES = {"POSTPONED"}


def usage():
    print("USAGE: nhl-season-results-by-team yyyyYYYY TEAM")
    print("Example: nhl-season-results-by-team 20252026 OTT")


def format_local_time(utc_string):
    start_utc = datetime.fromisoformat(utc_string.replace("Z", "+00:00"))
    start_local = start_utc.astimezone()
    return start_local.strftime("%b. %d, %Y %I:%M %p").replace(". 0", ". ")


def get_outcome(game, team_abbr):
    state = game.get("gameState", "")

    if state in POSTPONED_STATES:
        return "X"

    if state not in FINAL_STATES:
        return None

    away = game["awayTeam"]["abbrev"]
    home = game["homeTeam"]["abbrev"]
    away_score = game["awayTeam"].get("score", 0)
    home_score = game["homeTeam"].get("score", 0)

    if team_abbr == away:
        team_score = away_score
        opp_score = home_score
    elif team_abbr == home:
        team_score = home_score
        opp_score = away_score
    else:
        return None

    period_type = ""
    if "periodDescriptor" in game:
        period_type = game["periodDescriptor"].get("periodType", "")
    elif "gameOutcome" in game:
        period_type = game["gameOutcome"].get("lastPeriodType", "")

    is_ot = period_type in {"OT", "SO"}

    if team_score > opp_score:
        return "OTWIN" if is_ot else "WIN"
    elif team_score < opp_score:
        return "OTLOSS" if is_ot else "LOSS"
    else:
        return None


def should_list_game(game):
    state = game.get("gameState", "")
    return state in FINAL_STATES or state in POSTPONED_STATES


def print_team_season_results(season, team_abbr):
    client = NHLClient()

    schedule = client.schedule.team_season_schedule(
        team_abbr=team_abbr,
        season=season
    )

    games = schedule.get("games", [])

    if not games:
        print(f"No games found for {team_abbr} in {season}.")
        return

    print(f"{team_abbr} results for {season}:")

    found = False

    for game in games:
        if not should_list_game(game):
            continue

        away = game["awayTeam"]["abbrev"]
        home = game["homeTeam"]["abbrev"]
        away_score = game["awayTeam"].get("score", 0)
        home_score = game["homeTeam"].get("score", 0)
        when = format_local_time(game["startTimeUTC"])
        outcome = get_outcome(game, team_abbr)

        if outcome is None:
            continue

        print(f"{away} {away_score} @ {home} {home_score}  {when}  {outcome}")
        found = True

    if not found:
        print("No completed or postponed games found.")


def main():
    if len(sys.argv) != 3:
        usage()
        sys.exit(1)

    season = sys.argv[1]
    team_abbr = sys.argv[2].upper()

    if len(season) != 8 or not season.isdigit():
        usage()
        sys.exit(1)

    if len(team_abbr) != 3 or not team_abbr.isalpha():
        usage()
        sys.exit(1)

    print_team_season_results(season, team_abbr)


if __name__ == "__main__":
    main()
