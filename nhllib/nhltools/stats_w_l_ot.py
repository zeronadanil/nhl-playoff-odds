from nhlpy import NHLClient

TEAM_CODES = [
    "ANA", "BOS", "BUF", "CGY", "CAR", "CHI", "COL", "CBJ", "DAL", "DET",
    "EDM", "FLA", "LAK", "MIN", "MTL", "NSH", "NJD", "NYI", "NYR", "OTT",
    "PHI", "PIT", "SEA", "SJS", "STL", "TBL", "TOR", "UTA", "VAN", "VGK",
    "WPG", "WSH",
]

FINAL_STATES = {"OFF", "FINAL"}
REGULAR_SEASON_GAME_TYPE = 2


def usage():
    print("USAGE: nhl stats YYYYYYYY TEAM")
    print("Examples:")
    print(" nhl stats 20252026 OTT")
    print(" nhl stats 20252026 all")
    print(' nhl stats 20252026 "all teams"')


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


def pct(value, total):
    if total == 0:
        return "0.0%"
    return f"{value / total:.1%}"


def format_team_stats(team_code, season, stats):
    gp = stats["games_played"]
    return "\n".join([
        f"{team_code} regular season stats for {season}:",
        f"{'Games played:':22} {gp:>5}",
        f"{'Total wins:':22} {stats['wins']:>5} {pct(stats['wins'], gp):>6}",
        f"{'Total losses:':22} {stats['losses']:>5} {pct(stats['losses'], gp):>6}",
        f"{'Regulation wins:':22} {stats['regulation_wins']:>5} {pct(stats['regulation_wins'], gp):>6}",
        f"{'Regulation losses:':22} {stats['regulation_losses']:>5} {pct(stats['regulation_losses'], gp):>6}",
        f"{'OT wins:':22} {stats['ot_wins']:>5} {pct(stats['ot_wins'], gp):>6}",
        f"{'OT losses:':22} {stats['ot_losses']:>5} {pct(stats['ot_losses'], gp):>6}",
        f"{'Shootout wins:':22} {stats['shootout_wins']:>5} {pct(stats['shootout_wins'], gp):>6}",
        f"{'Shootout losses:':22} {stats['shootout_losses']:>5} {pct(stats['shootout_losses'], gp):>6}",
    ])


def format_league_stats(season, stats):
    gp = stats["games_played"]
    return "\n".join([
        f"NHL combined regular season stats for {season}:",
        f"{'Games played:':28} {gp:>5}",
        f"{'Home wins:':28} {stats['home_wins']:>5} {pct(stats['home_wins'], gp):>6}",
        f"{'Home losses:':28} {stats['home_losses']:>5} {pct(stats['home_losses'], gp):>6}",
        f"{'Overtime games:':28} {stats['overtime_games']:>5} {pct(stats['overtime_games'], gp):>6}",
        f"{'Shootout games:':28} {stats['shootout_games']:>5} {pct(stats['shootout_games'], gp):>6}",
        f"{'Regulation home wins:':28} {stats['regulation_wins']:>5} {pct(stats['regulation_wins'], gp):>6}",
        f"{'Regulation home losses:':28} {stats['regulation_losses']:>5} {pct(stats['regulation_losses'], gp):>6}",
        f"{'OT win by home:':28} {stats['ot_win_home']:>5} {pct(stats['ot_win_home'], gp):>6}",
        f"{'OT win by visitor:':28} {stats['ot_win_visitor']:>5} {pct(stats['ot_win_visitor'], gp):>6}",
        f"{'Shootout win by home:':28} {stats['shootout_win_home']:>5} {pct(stats['shootout_win_home'], gp):>6}",
        f"{'Shootout win by visitor:':28} {stats['shootout_win_visitor']:>5} {pct(stats['shootout_win_visitor'], gp):>6}",
    ])


def fetch_team_schedule(client, season, team_code):
    return client.schedule.team_season_schedule(
        team_abbr=team_code,
        season=season,
    )


def get_team_stats(season, team_code):
    client = NHLClient()
    schedule = fetch_team_schedule(client, season, team_code)
    games = schedule.get("games", [])
    stats = init_stats()

    for game in games:
        update_team_stats(stats, game, team_code)

    return stats


def get_league_stats(season):
    client = NHLClient()
    stats = init_stats()
    seen_game_ids = set()

    for team_code in TEAM_CODES:
        schedule = fetch_team_schedule(client, season, team_code)
        games = schedule.get("games", [])

        for game in games:
            game_id = game.get("id")
            if game_id in seen_game_ids:
                continue
            seen_game_ids.add(game_id)
            update_league_stats(stats, game)

    return stats


def main(argv=None):
    import sys

    if argv is None:
        argv = sys.argv[1:]

    if len(argv) != 2:
        usage()
        raise SystemExit(1)

    season = argv[0]
    team = argv[1].strip()

    if len(season) != 8 or not season.isdigit():
        usage()
        raise SystemExit(1)

    if team.lower() in {"all", "all teams"}:
        stats = get_league_stats(season)
        print(format_league_stats(season, stats))
        return

    team_code = team.upper()
    if team_code not in TEAM_CODES:
        print(f"Unknown team code: {team}")
        usage()
        raise SystemExit(1)

    stats = get_team_stats(season, team_code)
    print(format_team_stats(team_code, season, stats))


if __name__ == "__main__":
    main()
