#!/usr/bin/env python3

import argparse
from nhlpy import NHLClient


EAST_DIVISIONS = ["Atlantic", "Metropolitan"]
WEST_DIVISIONS = ["Central", "Pacific"]


def team_name(team):
    return team["teamName"]["default"]


def team_abbr(team):
    return team["teamAbbrev"]["default"]


def record(team):
    return f'{team["wins"]}-{team["losses"]}-{team["otLosses"]}'


def rw(team):
    return team.get("regulationWins", 0)


def row_value(team):
    return team.get("regulationPlusOtWins", 0)


def wins(team):
    return team.get("wins", 0)


def games_played(team):
    return team.get("gamesPlayed", 99)


def goal_diff(team):
    return team.get("goalDifferential", 0)


def goals_for(team):
    return team.get("goalFor", team.get("goalsFor", 0))


def sort_teams(teams):
    return sorted(
        teams,
        key=lambda t: (
            -t["points"],
            games_played(t),
            -rw(t),
            -row_value(t),
            -wins(t),
            -goal_diff(t),
            -goals_for(t),
            team_name(t)
        )
    )


def print_row(team, rank=None):
    rank_text = f"{rank:>2}. " if rank is not None else "    "
    print(
        f"{rank_text}"
        f"{team_abbr(team):<4} "
        f"{team_name(team):<24} "
        f"{team['points']:>3} pts  "
        f"{record(team):<10} "
        f"GP {team['gamesPlayed']:>2}  "
        f"RW {rw(team):>2}  "
        f"ROW {row_value(team):>2}  "
        f"DIFF {goal_diff(team):>4}  "
        f"GF {goals_for(team):>3}"
    )


def print_section(title, teams, ranked=True):
    print(title)
    for i, team in enumerate(teams, start=1):
        print_row(team, i if ranked else None)
    print()


def get_division_teams(standings, division_name):
    teams = [t for t in standings if t["divisionName"] == division_name]
    return sort_teams(teams)


def get_conference_teams(standings, conference_name):
    teams = [t for t in standings if t["conferenceName"] == conference_name]
    return sort_teams(teams)


def get_wildcard_groups(standings, conference_name):
    divisions = EAST_DIVISIONS if conference_name == "Eastern" else WEST_DIVISIONS
    remaining = []

    for division in divisions:
        teams = get_division_teams(standings, division)
        remaining.extend(teams[3:])

    remaining = sort_teams(remaining)
    wildcards = remaining[:2]
    in_hunt = remaining[2:]

    return wildcards, in_hunt


def print_wildcard_view(standings):
    atlantic = get_division_teams(standings, "Atlantic")
    metro = get_division_teams(standings, "Metropolitan")
    central = get_division_teams(standings, "Central")
    pacific = get_division_teams(standings, "Pacific")

    east_wc, east_hunt = get_wildcard_groups(standings, "Eastern")
    west_wc, west_hunt = get_wildcard_groups(standings, "Western")

    print("NHL CURRENT STANDINGS - WILDCARD")
    print()

    print_section("ATLANTIC DIVISION", atlantic[:3])
    print_section("METROPOLITAN DIVISION", metro[:3])
    print_section("EASTERN CONFERENCE WILD CARD", east_wc)

    if east_hunt:
        print_section("EASTERN CONFERENCE IN THE HUNT", east_hunt, ranked=False)

    print_section("CENTRAL DIVISION", central[:3])
    print_section("PACIFIC DIVISION", pacific[:3])
    print_section("WESTERN CONFERENCE WILD CARD", west_wc)

    if west_hunt:
        print_section("WESTERN CONFERENCE IN THE HUNT", west_hunt, ranked=False)


def print_division_view(standings):
    print("NHL CURRENT STANDINGS - DIVISION")
    print()

    for division in ["Atlantic", "Metropolitan", "Central", "Pacific"]:
        teams = get_division_teams(standings, division)
        print_section(f"{division.upper()} DIVISION", teams)


def print_conference_view(standings):
    print("NHL CURRENT STANDINGS - CONFERENCE")
    print()

    east = get_conference_teams(standings, "Eastern")
    west = get_conference_teams(standings, "Western")

    print_section("EASTERN CONFERENCE", east)
    print_section("WESTERN CONFERENCE", west)


def print_league_view(standings):
    print("NHL CURRENT STANDINGS - LEAGUE")
    print()
    all_teams = sort_teams(standings)
    print_section("NHL LEAGUE STANDINGS", all_teams)


def main():
    parser = argparse.ArgumentParser(
        prog="nhl-current-standings.py",
        description="Print current NHL standings in text form."
    )
    parser.add_argument(
        "view",
        choices=["wildcard", "division", "conference", "league"],
        help="Standings view to display"
    )

    args = parser.parse_args()

    client = NHLClient()
    data = client.standings.league_standings()
    standings = data.get("standings", [])

    if args.view == "wildcard":
        print_wildcard_view(standings)
    elif args.view == "division":
        print_division_view(standings)
    elif args.view == "conference":
        print_conference_view(standings)
    elif args.view == "league":
        print_league_view(standings)


if __name__ == "__main__":
    main()
