#!/usr/bin/env python3

import sys
from nhlpy import NHLClient


TEAM_CODES = [
    "ANA", "BOS", "BUF", "CGY", "CAR", "CHI", "COL", "CBJ", "DAL", "DET",
    "EDM", "FLA", "LAK", "MIN", "MTL", "NSH", "NJD", "NYI", "NYR", "OTT",
    "PHI", "PIT", "SEA", "SJS", "STL", "TBL", "TOR", "UTA", "VAN", "VGK",
    "WPG", "WSH"
]

FINAL_STATES = {"OFF", "FINAL"}
REGULAR_SEASON_GAME_TYPE = 2


def usage():
    print("USAGE: nhl-stats-regular-season-w-l-ot.py YYYYYYYY TEAM")
    print("Examples:")
    print("  nhl-stats-regular-season-w-l-ot.py 20242025 OTT")
    print("  nhl-stats-regular-season-w-l-ot.py 20242025 all")
    print('  nhl-stats-regular-season-w-l-ot.py 20242025 "all teams"')


def init_stats():
    return {
        "games_played": 0,
        "wins": 0,
        "losses": 0,
        "regulation_wins": 0,
        "regulation_losses": 0,
        "ot_wins": 0,
        "ot_losses": 0,
        "shootout_wins": 0,
        "shootout_losses": 0,
        "home_wins": 0,
        "home_losses": 0,
        "overtime_games": 0,
        "shootout_games": 0,
        "ot_win_home": 0,
        "ot_win_visitor": 0,
        "shootout_win_home": 0,
        "shootout_win_visitor": 0,
    }


def get_period_type(game):
    if "periodDescriptor" in game:
        return game["periodDescriptor"].get("periodType", "")
    if "gameOutcome" in game:
        return game["gameOutcome"].get("lastPeriodType", "")
    return ""


def is_regular_season(game):
    return game.get("gameType") == REGULAR_SEASON_GAME_TYPE


def is_final(game):
    return game.get("gameState", "") in FINAL_STATES


def update_team_stats(stats, game, team_code):
    if not is_regular_season(game):
        return
    if not is_final(game):
        return

    away = game["awayTeam"]["abbrev"]
    home = game["homeTeam"]["abbrev"]
    away_score = game["awayTeam"].get("score", 0)
    home_score = game["homeTeam"].get("score", 0)
    period_type = get_period_type(game)

    if team_code == away:
        team_score = away_score
        opp_score = home_score
    elif team_code == home:
        team_score = home_score
        opp_score = away_score
    else:
        return

    stats["games_played"] += 1

    if team_score > opp_score:
        stats["wins"] += 1
    elif team_score < opp_score:
        stats["losses"] += 1

    if period_type == "REG":
        if team_score > opp_score:
            stats["regulation_wins"] += 1
        elif team_score < opp_score:
            stats["regulation_losses"] += 1

    elif period_type == "OT":
        stats["overtime_games"] += 1
        if team_score > opp_score:
            stats["ot_wins"] += 1
        elif team_score < opp_score:
            stats["ot_losses"] += 1

    elif period_type == "SO":
        stats["overtime_games"] += 1
        stats["shootout_games"] += 1
        if team_score > opp_score:
            stats["shootout_wins"] += 1
        elif team_score < opp_score:
            stats["shootout_losses"] += 1


def update_league_stats(stats, game):
    if not is_regular_season(game):
        return
    if not is_final(game):
        return

    away_score = game["awayTeam"].get("score", 0)
    home_score = game["homeTeam"].get("score", 0)
    period_type = get_period_type(game)

    stats["games_played"] += 1

    if home_score > away_score:
        stats["home_wins"] += 1
    elif home_score < away_score:
        stats["home_losses"] += 1

    if period_type == "REG":
        if home_score > away_score:
            stats["regulation_wins"] += 1
        elif home_score < away_score:
            stats["regulation_losses"] += 1

    elif period_type == "OT":
        stats["overtime_games"] += 1
        if home_score > away_score:
            stats["ot_win_home"] += 1
        elif away_score > home_score:
            stats["ot_win_visitor"] += 1

    elif period_type == "SO":
        stats["overtime_games"] += 1
        stats["shootout_games"] += 1
        if home_score > away_score:
            stats["shootout_win_home"] += 1
        elif away_score > home_score:
            stats["shootout_win_visitor"] += 1


def print_team_stats(team_code, season, stats):
    print(f"{team_code} regular season stats for {season}:")
    print(f"Games played:         {stats['games_played']}")
    print(f"Total wins:           {stats['wins']}")
    print(f"Total losses:         {stats['losses']}")
    print(f"Regulation wins:      {stats['regulation_wins']}")
    print(f"Regulation losses:    {stats['regulation_losses']}")
    print(f"OT wins:              {stats['ot_wins']}")
    print(f"OT losses:            {stats['ot_losses']}")
    print(f"Shootout wins:        {stats['shootout_wins']}")
    print(f"Shootout losses:      {stats['shootout_losses']}")


def pct(value, total):
    if total == 0:
        return "0.0%"
    return f"{value / total:.1%}"

def print_team_stats(team_code, season, stats):
    gp = stats["games_played"]

    print(f"{team_code} regular season stats for {season}:")
    print(f"{'Games played:':22} {gp:>5}")
    print(f"{'Total wins:':22} {stats['wins']:>5}   {pct(stats['wins'], gp):>6}")
    print(f"{'Total losses:':22} {stats['losses']:>5}   {pct(stats['losses'], gp):>6}")
    print(f"{'Regulation wins:':22} {stats['regulation_wins']:>5}   {pct(stats['regulation_wins'], gp):>6}")
    print(f"{'Regulation losses:':22} {stats['regulation_losses']:>5}   {pct(stats['regulation_losses'], gp):>6}")
    print(f"{'OT wins:':22} {stats['ot_wins']:>5}   {pct(stats['ot_wins'], gp):>6}")
    print(f"{'OT losses:':22} {stats['ot_losses']:>5}   {pct(stats['ot_losses'], gp):>6}")
    print(f"{'Shootout wins:':22} {stats['shootout_wins']:>5}   {pct(stats['shootout_wins'], gp):>6}")
    print(f"{'Shootout losses:':22} {stats['shootout_losses']:>5}   {pct(stats['shootout_losses'], gp):>6}")


def fetch_team_schedule(client, season, team_code):
    return client.schedule.team_season_schedule(
        team_abbr=team_code,
        season=season
    )


def process_single_team(client, season, team_code):
    schedule = fetch_team_schedule(client, season, team_code)
    games = schedule.get("games", [])
    stats = init_stats()

    for game in games:
        update_team_stats(stats, game, team_code)

    print_team_stats(team_code, season, stats)


def process_all_teams(client, season):
    league_stats = init_stats()
    seen_game_ids = set()

    for team_code in TEAM_CODES:
        schedule = fetch_team_schedule(client, season, team_code)
        games = schedule.get("games", [])

        for game in games:
            game_id = game.get("id")
            if game_id in seen_game_ids:
                continue
            seen_game_ids.add(game_id)
            update_league_stats(league_stats, game)

    print_league_stats(season, league_stats)


def main():
    if len(sys.argv) != 3:
        usage()
        sys.exit(1)

    season = sys.argv[1]
    team = sys.argv[2].strip()

    if len(season) != 8 or not season.isdigit():
        usage()
        sys.exit(1)

    client = NHLClient()

    if team.lower() in {"all", "all teams"}:
        process_all_teams(client, season)
        return

    team_code = team.upper()
    if team_code not in TEAM_CODES:
        print(f"Unknown team code: {team}")
        usage()
        sys.exit(1)

    process_single_team(client, season, team_code)


if __name__ == "__main__":
    main()
