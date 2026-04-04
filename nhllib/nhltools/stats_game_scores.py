from collections import Counter
from dataclasses import asdict, dataclass
from typing import List

from nhlpy import NHLClient


TEAM_CODES = [
    "ANA", "BOS", "BUF", "CGY", "CAR", "CHI", "COL", "CBJ", "DAL", "DET",
    "EDM", "FLA", "LAK", "MIN", "MTL", "NSH", "NJD", "NYI", "NYR", "OTT",
    "PHI", "PIT", "SEA", "SJS", "STL", "TBL", "TOR", "UTA", "VAN", "VGK",
    "WPG", "WSH",
]

REGULAR_SEASON_GAME_TYPE = 2
FINAL_STATES = {"OFF", "FINAL"}


@dataclass
class GameScore:
    game_id: int
    date: str
    away_team: str
    home_team: str
    away_score: int
    home_score: int
    win_type: str


@dataclass
class RemainingGame:
    game_id: int
    game_date: str
    home_team: str
    visiting_team: str


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


def normalize_win_type(game):
    period_type = get_period_type(game)
    if period_type == "OT":
        return "OT"
    if period_type == "SO":
        return "SO"
    return "REG"


def fetch_team_schedule(client, season, team_code):
    schedule = client.schedule.team_season_schedule(
        team_abbr=team_code,
        season=season,
    )
    return schedule.get("games", [])


def game_to_record(game):
    return GameScore(
        game_id=game["id"],
        date=game["startTimeUTC"][:10],
        away_team=game["awayTeam"]["abbrev"],
        home_team=game["homeTeam"]["abbrev"],
        away_score=game["awayTeam"].get("score", 0),
        home_score=game["homeTeam"].get("score", 0),
        win_type=normalize_win_type(game),
    )


def remaining_game_to_record(game):
    return RemainingGame(
        game_id=game["id"],
        game_date=game["startTimeUTC"][:10],
        home_team=game["homeTeam"]["abbrev"],
        visiting_team=game["awayTeam"]["abbrev"],
    )


def get_season_game_scores(season) -> List[GameScore]:
    client = NHLClient()
    seen_game_ids = set()
    results = []

    for team_code in TEAM_CODES:
        games = fetch_team_schedule(client, season, team_code)

        for game in games:
            game_id = game.get("id")

            if game_id in seen_game_ids:
                continue
            if not is_regular_season(game):
                continue
            if not is_final(game):
                continue

            seen_game_ids.add(game_id)
            results.append(game_to_record(game))

    results.sort(key=lambda g: (g.date, g.game_id))
    return results


def get_season_game_scores_as_dicts(season):
    return [asdict(game) for game in get_season_game_scores(season)]


def all_remaining_games(season) -> List[RemainingGame]:
    client = NHLClient()
    seen_game_ids = set()
    results = []

    for team_code in TEAM_CODES:
        games = fetch_team_schedule(client, season, team_code)

        for game in games:
            game_id = game.get("id")

            if game_id in seen_game_ids:
                continue
            if not is_regular_season(game):
                continue
            if is_final(game):
                continue

            seen_game_ids.add(game_id)
            results.append(remaining_game_to_record(game))

    results.sort(key=lambda g: (g.game_date, g.game_id))
    return results


def all_remaining_games_as_dicts(season):
    return [asdict(game) for game in all_remaining_games(season)]


def validate_team_or_mode(value):
    text = value.strip().upper()

    if text in {"ALL", "ALL TEAMS"}:
        return "ALL"
    if text == "HOME":
        return "HOME"
    if text in {"VISITOR", "AWAY"}:
        return "VISITOR"
    if text in TEAM_CODES:
        return text

    raise ValueError(f"unknown team or mode: {value}")


def histogram_goals_by_team(season, team_code):
    mode = validate_team_or_mode(team_code)
    games = get_season_game_scores(season)

    gf_values = []
    ga_values = []

    if mode == "ALL":
        for game in games:
            gf_values.append(game.home_score)
            ga_values.append(game.away_score)

            gf_values.append(game.away_score)
            ga_values.append(game.home_score)

    elif mode == "HOME":
        for game in games:
            gf_values.append(game.home_score)
            ga_values.append(game.away_score)

    elif mode == "VISITOR":
        for game in games:
            gf_values.append(game.away_score)
            ga_values.append(game.home_score)

    else:
        for game in games:
            if game.home_team == mode:
                gf_values.append(game.home_score)
                ga_values.append(game.away_score)
            elif game.away_team == mode:
                gf_values.append(game.away_score)
                ga_values.append(game.home_score)

    gf_hist = dict(sorted(Counter(gf_values).items()))
    ga_hist = dict(sorted(Counter(ga_values).items()))

    return {
        "season": season,
        "team": mode,
        "games_played": len(gf_values),
        "gf_histogram": gf_hist,
        "ga_histogram": ga_hist,
    }


def format_all_remaining_games(season):
    games = all_remaining_games(season)

    if not games:
        return f"No remaining regular season games for {season}."

    lines = [
        f"NHL REMAINING REGULAR SEASON GAMES FOR {season}",
        "",
        f"{'DATE':<12} {'VISITOR':<7} {'HOME':<7} {'GAME ID':>10}",
        f"{'-' * 12} {'-' * 7} {'-' * 7} {'-' * 10}",
    ]

    for game in games:
        lines.append(
            f"{game.game_date:<12} "
            f"{game.visiting_team:<7} "
            f"{game.home_team:<7} "
            f"{game.game_id:>10}"
        )

    return "\n".join(lines)

def format_all_remaining_games_grouped(season):
    games = all_remaining_games(season)

    if not games:
        return f"No remaining regular season games for {season}."

    lines = [f"NHL REMAINING REGULAR SEASON GAMES FOR {season}", ""]

    current_date = None

    for game in games:
        if game.game_date != current_date:
            if current_date is not None:
                lines.append("")
            current_date = game.game_date
            lines.append(current_date)

        lines.append(
            f"  {game.visiting_team:>3} at {game.home_team:<3}   {game.game_id}"
        )

    return "\n".join(lines)
