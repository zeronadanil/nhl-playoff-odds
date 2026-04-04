import argparse
from datetime import datetime

from nhlpy import NHLClient


FINAL_STATES = {"OFF", "FINAL"}
POSTPONED_STATES = {"POSTPONED"}


def usage():
    print("USAGE: nhl season-results-by-team YYYYYYYY TEAM")
    print("Example:")
    print(" nhl season-results-by-team 20252026 OTT")


def format_local_time(utc_string):
    start_utc = datetime.fromisoformat(utc_string.replace("Z", "+00:00"))
    start_local = start_utc.astimezone()
    return start_local.strftime("%b. %d, %Y %I:%M %p").replace(". 0", ". ")


def fetch_team_schedule(season, team_abbr):
    client = NHLClient()
    schedule = client.schedule.team_season_schedule(
        team_abbr=team_abbr.upper(),
        season=season,
    )
    return schedule.get("games", [])


def get_period_type(game):
    if "periodDescriptor" in game:
        return game["periodDescriptor"].get("periodType", "")
    if "gameOutcome" in game:
        return game["gameOutcome"].get("lastPeriodType", "")
    return ""


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

    period_type = get_period_type(game)
    is_ot = period_type in {"OT", "SO"}

    if team_score > opp_score:
        return "OTWIN" if is_ot else "WIN"
    if team_score < opp_score:
        return "OTLOSS" if is_ot else "LOSS"
    return None


def should_list_game(game):
    state = game.get("gameState", "")
    return state in FINAL_STATES or state in POSTPONED_STATES


def get_team_results(season, team_abbr):
    games = fetch_team_schedule(season, team_abbr)
    results = []

    for game in games:
        if not should_list_game(game):
            continue

        outcome = get_outcome(game, team_abbr.upper())
        if outcome is None:
            continue

        results.append((game, outcome))

    return results


def format_result_line(game, outcome):
    away = game["awayTeam"]["abbrev"]
    home = game["homeTeam"]["abbrev"]
    away_score = game["awayTeam"].get("score", 0)
    home_score = game["homeTeam"].get("score", 0)
    when = format_local_time(game["startTimeUTC"])
    return f"{away} {away_score} @ {home} {home_score} {when} {outcome}"


def format_team_results(season, team_abbr, results):
    team_abbr = team_abbr.upper()
    lines = [f"{team_abbr} results for {season}:"]

    if not results:
        lines.append("No completed or postponed games found.")
        return "\n".join(lines)

    for game, outcome in results:
        lines.append(format_result_line(game, outcome))

    return "\n".join(lines)


def validate_inputs(season, team_abbr):
    if len(season) != 8 or not season.isdigit():
        raise ValueError("season must be in YYYYYYYY format, for example 20252026")

    if len(team_abbr) != 3 or not team_abbr.isalpha():
        raise ValueError("team must be a three-letter abbreviation, for example OTT")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="nhl season-results-by-team",
        description="Print season results for an NHL team.",
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

    results = get_team_results(args.season, args.team)
    print(format_team_results(args.season, args.team, results))


if __name__ == "__main__":
    main()
