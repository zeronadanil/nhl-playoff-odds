import secrets
from datetime import datetime
from time import perf_counter
from dataclasses import asdict, dataclass
from typing import Dict, List

from nhltools.stats_game_scores import (
    GameScore,
    RemainingGame,
    all_remaining_games,
    get_season_game_scores,
)

TEAM_TO_DIVISION = {
    "BOS": "Atlantic",
    "BUF": "Atlantic",
    "DET": "Atlantic",
    "FLA": "Atlantic",
    "MTL": "Atlantic",
    "OTT": "Atlantic",
    "TBL": "Atlantic",
    "TOR": "Atlantic",
    "CAR": "Metropolitan",
    "CBJ": "Metropolitan",
    "NJD": "Metropolitan",
    "NYI": "Metropolitan",
    "NYR": "Metropolitan",
    "PHI": "Metropolitan",
    "PIT": "Metropolitan",
    "WSH": "Metropolitan",
    "CHI": "Central",
    "COL": "Central",
    "DAL": "Central",
    "MIN": "Central",
    "NSH": "Central",
    "STL": "Central",
    "UTA": "Central",
    "WPG": "Central",
    "ANA": "Pacific",
    "CGY": "Pacific",
    "EDM": "Pacific",
    "LAK": "Pacific",
    "SEA": "Pacific",
    "SJS": "Pacific",
    "VAN": "Pacific",
    "VGK": "Pacific",
}

DIVISION_TO_CONFERENCE = {
    "Atlantic": "East",
    "Metropolitan": "East",
    "Central": "West",
    "Pacific": "West",
}


@dataclass
class RegOtSoStats:
    team: str
    games_played: int
    regulation_wins: int
    regulation_losses: int
    ot_wins: int
    ot_losses: int
    so_wins: int
    so_losses: int
    visiting_regulation_win: int
    visiting_regulation_loss: int
    visiting_ot_win: int
    visiting_ot_loss: int
    visiting_so_win: int
    visiting_so_loss: int
    home_regulation_win: int
    home_regulation_loss: int
    home_ot_win: int
    home_ot_loss: int
    home_so_win: int
    home_so_loss: int


@dataclass
class TeamStanding:
    team: str
    division: str
    conference: str
    games_played: int
    wins: int
    losses: int
    ot_losses: int
    points: int
    regulation_wins: int
    row: int
    goals_for: int
    goals_against: int
    goal_diff: int


def _init_team_record(team_code: str) -> TeamStanding:
    division = TEAM_TO_DIVISION[team_code]
    conference = DIVISION_TO_CONFERENCE[division]
    return TeamStanding(
        team=team_code,
        division=division,
        conference=conference,
        games_played=0,
        wins=0,
        losses=0,
        ot_losses=0,
        points=0,
        regulation_wins=0,
        row=0,
        goals_for=0,
        goals_against=0,
        goal_diff=0,
    )


def _build_empty_standings() -> Dict[str, TeamStanding]:
    return {team: _init_team_record(team) for team in TEAM_TO_DIVISION}


def _apply_game_result(standings: Dict[str, TeamStanding], game: GameScore) -> None:
    away = standings[game.away_team]
    home = standings[game.home_team]

    away.games_played += 1
    home.games_played += 1

    away.goals_for += game.away_score
    away.goals_against += game.home_score
    home.goals_for += game.home_score
    home.goals_against += game.away_score

    away.goal_diff = away.goals_for - away.goals_against
    home.goal_diff = home.goals_for - home.goals_against

    away_won = game.away_score > game.home_score
    home_won = game.home_score > game.away_score

    if away_won:
        away.wins += 1
        away.points += 2

        if game.win_type == "REG":
            away.regulation_wins += 1
            away.row += 1
            home.losses += 1
        elif game.win_type == "OT":
            away.row += 1
            home.ot_losses += 1
            home.points += 1
        elif game.win_type == "SO":
            home.ot_losses += 1
            home.points += 1

    elif home_won:
        home.wins += 1
        home.points += 2

        if game.win_type == "REG":
            home.regulation_wins += 1
            home.row += 1
            away.losses += 1
        elif game.win_type == "OT":
            home.row += 1
            away.ot_losses += 1
            away.points += 1
        elif game.win_type == "SO":
            away.ot_losses += 1
            away.points += 1


def _standings_sort_key(team: TeamStanding):
    return (
        -team.points,
        -team.regulation_wins,
        -team.row,
        -team.wins,
        -team.goal_diff,
        -team.goals_for,
        team.team,
    )

def normalize_team_code(team: str) -> str:
    aliases = {
        "WAS": "WSH",
    }
    return aliases.get(team.strip().upper(), team.strip().upper())

def validate_team_code(team: str) -> str:
    team = normalize_team_code(team)
    if team not in TEAM_TO_DIVISION:
        valid_codes = ", ".join(sorted(TEAM_TO_DIVISION))
        raise ValueError(f"unknown team code: {team}. valid team codes: {valid_codes}")
    return team

def standings_from_game_scores(games: List[GameScore]) -> List[TeamStanding]:
    standings = _build_empty_standings()

    for game in games:
        _apply_game_result(standings, game)

    return sorted(standings.values(), key=_standings_sort_key)


def get_team_standings(season: str) -> List[TeamStanding]:
    games = get_season_game_scores(season)
    return standings_from_game_scores(games)


def wildcard_standings(team_rows: List[TeamStanding]):
    conferences: Dict[str, List[TeamStanding]] = {}
    for row in team_rows:
        conferences.setdefault(row.conference, []).append(row)

    result = {}

    for conference, conf_rows in conferences.items():
        divisions: Dict[str, List[TeamStanding]] = {}
        for row in conf_rows:
            divisions.setdefault(row.division, []).append(row)

        sorted_divisions = {
            division: sorted(rows, key=_standings_sort_key)
            for division, rows in divisions.items()
        }

        division_leaders = {}
        division_spots = {}
        automatic_qualifiers = []

        for division, rows in sorted_divisions.items():
            top_three = rows[:3]
            division_spots[division] = [asdict(team) for team in top_three]

            if top_three:
                division_leaders[division] = asdict(top_three[0])

            automatic_qualifiers.extend(top_three)

        auto_teams = {team.team for team in automatic_qualifiers}
        remaining = [team for team in conf_rows if team.team not in auto_teams]
        remaining_sorted = sorted(remaining, key=_standings_sort_key)

        wildcards = [asdict(team) for team in remaining_sorted[:2]]
        outside = [asdict(team) for team in remaining_sorted[2:]]

        result[conference] = {
            "division_leaders": division_leaders,
            "division_spots": division_spots,
            "wildcards": wildcards,
            "outside": outside,
        }

    return result


def get_wildcard_standings(season: str):
    standings = get_team_standings(season)
    return wildcard_standings(standings)


def _format_record(team: dict) -> str:
    return f"{team['wins']}-{team['losses']}-{team['ot_losses']}"


def _format_team_line(team: dict, rank=None) -> str:
    rank_text = f"{rank:>2}. " if rank is not None else " "
    return (
        f"{rank_text}"
        f"{team['team']:<4} "
        f"{team['points']:>3} pts "
        f"{_format_record(team):<8} "
        f"GP {team['games_played']:>2} "
        f"RW {team['regulation_wins']:>2} "
        f"ROW {team['row']:>2} "
        f"DIFF {team['goal_diff']:>+4}"
    )


def _format_section(title: str, teams: List[dict], ranked: bool = True) -> List[str]:
    lines = [title]
    for index, team in enumerate(teams, start=1):
        lines.append(_format_team_line(team, index if ranked else None))
    lines.append("")
    return lines


def _standings_dict_sort_key(team: dict):
    return (
        -team["points"],
        -team["regulation_wins"],
        -team["row"],
        -team["wins"],
        -team["goal_diff"],
        -team["goals_for"],
        team["team"],
    )


def _first_round_matchups_for_conference(conference_data: dict) -> List[str]:
    division_spots = conference_data["division_spots"]
    wildcards = conference_data["wildcards"]

    if len(wildcards) < 2:
        return ["Not enough teams to determine first-round matchups"]

    division_winners = []
    for division, teams in division_spots.items():
        if len(teams) >= 3:
            division_winners.append((division, teams[0]))

    if len(division_winners) < 2:
        return ["Not enough division winners to determine first-round matchups"]

    division_winners.sort(key=lambda item: _standings_dict_sort_key(item[1]))

    top_division, top_winner = division_winners[0]
    other_division, other_winner = division_winners[1]

    top_division_teams = division_spots[top_division]
    other_division_teams = division_spots[other_division]

    return [
        f"{top_winner['team']} (1) vs {wildcards[1]['team']} (WC2)",
        f"{other_winner['team']} (1) vs {wildcards[0]['team']} (WC1)",
        f"{top_division_teams[1]['team']} (2) vs {top_division_teams[2]['team']} (3)",
        f"{other_division_teams[1]['team']} (2) vs {other_division_teams[2]['team']} (3)",
    ]


def format_first_round_matchups_from_standings(standings_rows) -> str:
    wc = wildcard_standings(standings_rows)
    lines = ["NHL FIRST ROUND MATCHUPS IF SEASON ENDS AS PROJECTED", ""]

    for conference in ("East", "West"):
        lines.append(f"=== {conference.upper()}ERN CONFERENCE ===")
        lines.append("")

        for matchup in _first_round_matchups_for_conference(wc[conference]):
            lines.append(matchup)

        lines.append("")

    return "\n".join(lines)


def print_first_round_matchups_from_standings(standings_rows):
    print(format_first_round_matchups_from_standings(standings_rows))


def _first_round_matchups_from_odds_conference_rows(rows: list) -> List[str]:
    divisions = {}
    for row in rows:
        divisions.setdefault(row["division"], []).append(row)

    sorted_divisions = {
        division: sorted(rows, key=lambda r: (-r["percent_in"], r["team"]))
        for division, rows in divisions.items()
    }

    division_names = sorted(sorted_divisions.keys())
    automatic_qualifiers = []

    for division in division_names:
        automatic_qualifiers.extend(sorted_divisions[division][:3])

    auto_teams = {row["team"] for row in automatic_qualifiers}
    remaining = [row for row in rows if row["team"] not in auto_teams]
    remaining_sorted = sorted(remaining, key=lambda r: (-r["percent_in"], r["team"]))

    wildcards = remaining_sorted[:2]

    if len(division_names) < 2 or len(wildcards) < 2:
        return ["Not enough teams to determine first-round matchups"]

    division_winners = [
        (division, sorted_divisions[division][0])
        for division in division_names
        if len(sorted_divisions[division]) >= 3
    ]

    if len(division_winners) < 2:
        return ["Not enough division winners to determine first-round matchups"]

    division_winners.sort(key=lambda item: (-item[1]["percent_in"], item[1]["team"]))

    top_division, top_winner = division_winners[0]
    other_division, other_winner = division_winners[1]

    top_division_teams = sorted_divisions[top_division]
    other_division_teams = sorted_divisions[other_division]

    return [
        f"{top_winner['team']} (1) vs {wildcards[1]['team']} (WC2)",
        f"{other_winner['team']} (1) vs {wildcards[0]['team']} (WC1)",
        f"{top_division_teams[1]['team']} (2) vs {top_division_teams[2]['team']} (3)",
        f"{other_division_teams[1]['team']} (2) vs {other_division_teams[2]['team']} (3)",
    ]


def format_first_round_matchups_from_odds(results_by_conference) -> str:
    lines = ["NHL FIRST ROUND MATCHUPS BASED ON PLAYOFF ODDS", ""]

    for conference in ("East", "West"):
        lines.append(f"=== {conference.upper()}ERN CONFERENCE ===")
        lines.append("")

        for matchup in _first_round_matchups_from_odds_conference_rows(
            results_by_conference[conference]
        ):
            lines.append(matchup)

        lines.append("")

    return "\n".join(lines)


def print_first_round_matchups_from_odds(results_by_conference):
    print(format_first_round_matchups_from_odds(results_by_conference))


def format_wildcard_standings(season: str) -> str:
    standings = get_wildcard_standings(season)
    lines = [f"NHL WILDCARD STANDINGS FOR {season}", ""]

    east = standings["East"]
    west = standings["West"]

    east_divisions = sorted(east["division_spots"].keys())
    west_divisions = sorted(west["division_spots"].keys())

    for division in east_divisions:
        lines.extend(
            _format_section(
                f"{division.upper()} DIVISION",
                east["division_spots"][division],
            )
        )

    lines.extend(
        _format_section(
            "EASTERN CONFERENCE WILD CARD",
            east["wildcards"],
        )
    )

    if east["outside"]:
        lines.extend(
            _format_section(
                "EASTERN CONFERENCE OUTSIDE",
                east["outside"],
                ranked=False,
            )
        )

    for division in west_divisions:
        lines.extend(
            _format_section(
                f"{division.upper()} DIVISION",
                west["division_spots"][division],
            )
        )

    lines.extend(
        _format_section(
            "WESTERN CONFERENCE WILD CARD",
            west["wildcards"],
        )
    )

    if west["outside"]:
        lines.extend(
            _format_section(
                "WESTERN CONFERENCE OUTSIDE",
                west["outside"],
                ranked=False,
            )
        )

    return "\n".join(lines)


def _init_reg_ot_so_stats(team_code: str) -> RegOtSoStats:
    return RegOtSoStats(
        team=team_code,
        games_played=0,
        regulation_wins=0,
        regulation_losses=0,
        ot_wins=0,
        ot_losses=0,
        so_wins=0,
        so_losses=0,
        visiting_regulation_win=0,
        visiting_regulation_loss=0,
        visiting_ot_win=0,
        visiting_ot_loss=0,
        visiting_so_win=0,
        visiting_so_loss=0,
        home_regulation_win=0,
        home_regulation_loss=0,
        home_ot_win=0,
        home_ot_loss=0,
        home_so_win=0,
        home_so_loss=0,
    )


def _apply_reg_ot_so_result(stats: Dict[str, RegOtSoStats], game: GameScore) -> None:
    away = stats[game.away_team]
    home = stats[game.home_team]

    away.games_played += 1
    home.games_played += 1

    away_won = game.away_score > game.home_score
    home_won = game.home_score > game.away_score

    if game.win_type == "REG":
        if away_won:
            away.regulation_wins += 1
            away.visiting_regulation_win += 1
            home.regulation_losses += 1
            home.home_regulation_loss += 1
        elif home_won:
            home.regulation_wins += 1
            home.home_regulation_win += 1
            away.regulation_losses += 1
            away.visiting_regulation_loss += 1

    elif game.win_type == "OT":
        if away_won:
            away.ot_wins += 1
            away.visiting_ot_win += 1
            home.ot_losses += 1
            home.home_ot_loss += 1
        elif home_won:
            home.ot_wins += 1
            home.home_ot_win += 1
            away.ot_losses += 1
            away.visiting_ot_loss += 1

    elif game.win_type == "SO":
        if away_won:
            away.so_wins += 1
            away.visiting_so_win += 1
            home.so_losses += 1
            home.home_so_loss += 1
        elif home_won:
            home.so_wins += 1
            home.home_so_win += 1
            away.so_losses += 1
            away.visiting_so_loss += 1


def reg_ot_so(past_games: List[GameScore]):
    stats = {team: _init_reg_ot_so_stats(team) for team in TEAM_TO_DIVISION}

    for game in past_games:
        _apply_reg_ot_so_result(stats, game)

    all_stats = RegOtSoStats(
        team="ALL",
        games_played=0,
        regulation_wins=0,
        regulation_losses=0,
        ot_wins=0,
        ot_losses=0,
        so_wins=0,
        so_losses=0,
        visiting_regulation_win=0,
        visiting_regulation_loss=0,
        visiting_ot_win=0,
        visiting_ot_loss=0,
        visiting_so_win=0,
        visiting_so_loss=0,
        home_regulation_win=0,
        home_regulation_loss=0,
        home_ot_win=0,
        home_ot_loss=0,
        home_so_win=0,
        home_so_loss=0,
    )

    for team_code in sorted(stats.keys()):
        team_stats = stats[team_code]
        all_stats.games_played += team_stats.games_played
        all_stats.regulation_wins += team_stats.regulation_wins
        all_stats.regulation_losses += team_stats.regulation_losses
        all_stats.ot_wins += team_stats.ot_wins
        all_stats.ot_losses += team_stats.ot_losses
        all_stats.so_wins += team_stats.so_wins
        all_stats.so_losses += team_stats.so_losses

        all_stats.visiting_regulation_win += team_stats.visiting_regulation_win
        all_stats.visiting_regulation_loss += team_stats.visiting_regulation_loss
        all_stats.visiting_ot_win += team_stats.visiting_ot_win
        all_stats.visiting_ot_loss += team_stats.visiting_ot_loss
        all_stats.visiting_so_win += team_stats.visiting_so_win
        all_stats.visiting_so_loss += team_stats.visiting_so_loss

        all_stats.home_regulation_win += team_stats.home_regulation_win
        all_stats.home_regulation_loss += team_stats.home_regulation_loss
        all_stats.home_ot_win += team_stats.home_ot_win
        all_stats.home_ot_loss += team_stats.home_ot_loss
        all_stats.home_so_win += team_stats.home_so_win
        all_stats.home_so_loss += team_stats.home_so_loss

    return {
        "teams": {team: asdict(stats[team]) for team in sorted(stats.keys())},
        "all": asdict(all_stats),
    }


def build_goal_histograms_from_games(past_games: List[GameScore]):
    result = {}

    for team in TEAM_TO_DIVISION:
        gf_values = []
        ga_values = []

        for game in past_games:
            if game.home_team == team:
                gf_values.append(game.home_score)
                ga_values.append(game.away_score)
            elif game.away_team == team:
                gf_values.append(game.away_score)
                ga_values.append(game.home_score)

        gf_hist = {}
        ga_hist = {}

        for goals in gf_values:
            gf_hist[goals] = gf_hist.get(goals, 0) + 1

        for goals in ga_values:
            ga_hist[goals] = ga_hist.get(goals, 0) + 1

        result[team] = {
            "season": None,
            "team": team,
            "games_played": len(gf_values),
            "gf_histogram": dict(sorted(gf_hist.items())),
            "ga_histogram": dict(sorted(ga_hist.items())),
        }

    return result


def decide_regulation_or_extra(regulation: int, extra: int):
    total = regulation + extra

    if total == 0:
        return {
            "random_number": 0,
            "random_total": 0,
            "outcome_type": "unknown",
        }

    random_number = secrets.randbelow(total) + 1
    outcome_type = "regulation" if random_number <= regulation else "extra"

    return {
        "random_number": random_number,
        "random_total": total,
        "outcome_type": outcome_type,
    }


def weighted_goal_draw(histogram):
    total_weight = sum(histogram.values())

    if total_weight == 0:
        return 0

    random_number = secrets.randbelow(total_weight) + 1
    running_total = 0

    for goals, weight in sorted(histogram.items()):
        running_total += weight
        if random_number <= running_total:
            return int(goals)

    return int(max(histogram))

def weighted_losing_regulation_goals(histogram, winning_goals):
    losing_histogram = {
        int(goals): weight
        for goals, weight in histogram.items()
        if int(goals) < winning_goals
    }

    if not losing_histogram:
        return max(0, winning_goals - 1)

    return weighted_goal_draw(losing_histogram)

def decide_extra_winner(
    game: RemainingGame,
    home_ot_w: int,
    home_so_w: int,
    home_ot_l: int,
    home_so_l: int,
    visiting_ot_w: int,
    visiting_so_w: int,
    visiting_ot_l: int,
    visiting_so_l: int,
):
    home_ot = home_ot_w + visiting_ot_l
    home_so = home_so_w + visiting_so_l
    visiting_ot = home_ot_l + visiting_ot_w
    visiting_so = home_so_l + visiting_so_w

    extra_total = home_ot + home_so + visiting_ot + visiting_so

    if extra_total == 0:
        return {
            "winner_random": 0,
            "winner_total": 0,
            "winner": "unknown",
            "loser": "unknown",
            "outcome_subtype": "EXTRA",
            "home_odds": 0,
            "visiting_odds": 0,
        }

    winner_random = secrets.randbelow(extra_total) + 1

    if winner_random <= home_ot:
        winner = game.home_team
        loser = game.visiting_team
        outcome_subtype = "OT"
    elif winner_random <= home_ot + home_so:
        winner = game.home_team
        loser = game.visiting_team
        outcome_subtype = "SO"
    elif winner_random <= home_ot + home_so + visiting_ot:
        winner = game.visiting_team
        loser = game.home_team
        outcome_subtype = "OT"
    else:
        winner = game.visiting_team
        loser = game.home_team
        outcome_subtype = "SO"

    return {
        "winner_random": winner_random,
        "winner_total": extra_total,
        "winner": winner,
        "loser": loser,
        "outcome_subtype": outcome_subtype,
        "home_odds": home_ot + home_so,
        "visiting_odds": visiting_ot + visiting_so,
    }

def generate_extra_score(
    winner: str,
    game: RemainingGame,
    home_goal_hist,
    visiting_goal_hist,
    outcome_subtype: str,
):
    if winner == game.home_team:
        loser = game.visiting_team
        losing_goals = weighted_goal_draw(visiting_goal_hist["gf_histogram"])
    elif winner == game.visiting_team:
        loser = game.home_team
        losing_goals = weighted_goal_draw(home_goal_hist["gf_histogram"])
    else:
        return {
            "winner": "unknown",
            "loser": "unknown",
            "winning_goals": 0,
            "losing_goals": 0,
        }

    winning_goals = losing_goals + 1

    return {
        "winner": winner,
        "loser": loser,
        "winning_goals": winning_goals,
        "losing_goals": losing_goals,
        "outcome_subtype": outcome_subtype,
    }


def sim_game_result(
    game: RemainingGame,
    reg_ot_so_stats,
    goal_histograms,
):
    home_stats = reg_ot_so_stats["teams"][game.home_team]
    visiting_stats = reg_ot_so_stats["teams"][game.visiting_team]

    home_goal_hist = goal_histograms[game.home_team]
    visiting_goal_hist = goal_histograms[game.visiting_team]

    visiting_reg_w = visiting_stats["visiting_regulation_win"]
    visiting_reg_l = visiting_stats["visiting_regulation_loss"]
    visiting_ot_w = visiting_stats["visiting_ot_win"]
    visiting_ot_l = visiting_stats["visiting_ot_loss"]
    visiting_so_w = visiting_stats["visiting_so_win"]
    visiting_so_l = visiting_stats["visiting_so_loss"]

    home_reg_w = home_stats["home_regulation_win"]
    home_reg_l = home_stats["home_regulation_loss"]
    home_ot_w = home_stats["home_ot_win"]
    home_ot_l = home_stats["home_ot_loss"]
    home_so_w = home_stats["home_so_win"]
    home_so_l = home_stats["home_so_loss"]

    regulation = (
        visiting_reg_w
        + visiting_reg_l
        + home_reg_w
        + home_reg_l
    )

    extra = (
        visiting_ot_w
        + visiting_ot_l
        + visiting_so_w
        + visiting_so_l
        + home_ot_w
        + home_ot_l
        + home_so_w
        + home_so_l
    )

    decision = decide_regulation_or_extra(regulation, extra)

    home_odds = 0
    visiting_odds = 0
    winner_total = 0
    winner_random = 0
    winner = "unknown"
    loser = "unknown"
    winning_goals = 0
    losing_goals = 0
    outcome_subtype = 'ERR';

    if decision["outcome_type"] == "regulation":
        home_odds = home_reg_w + visiting_reg_l
        visiting_odds = home_reg_l + visiting_reg_w

        winner_total = home_odds + visiting_odds
        outcome_subtype = 'REG';

        if winner_total > 0:
            winner_random = secrets.randbelow(winner_total) + 1

            if winner_random <= home_odds:
                winner = game.home_team
                loser = game.visiting_team
                winning_goals = weighted_goal_draw(home_goal_hist["gf_histogram"])
                losing_goals = weighted_losing_regulation_goals(
                    visiting_goal_hist["gf_histogram"],
                    winning_goals,
                )
            else:
                winner = game.visiting_team
                loser = game.home_team
                winning_goals = weighted_goal_draw(visiting_goal_hist["gf_histogram"])
                losing_goals = weighted_losing_regulation_goals(
                    home_goal_hist["gf_histogram"],
                    winning_goals,
                )
    else:
        extra_result = decide_extra_winner(
            game,
            home_ot_w,
            home_so_w,
            home_ot_l,
            home_so_l,
            visiting_ot_w,
            visiting_so_w,
            visiting_ot_l,
            visiting_so_l,
        )

        winner_random = extra_result["winner_random"]
        winner_total = extra_result["winner_total"]
        winner = extra_result["winner"]
        loser = extra_result["loser"]
        outcome_subtype = extra_result["outcome_subtype"]
        home_odds = extra_result["home_odds"]
        visiting_odds = extra_result["visiting_odds"]

        extra_score = generate_extra_score(
            winner,
            game,
            home_goal_hist,
            visiting_goal_hist,
            outcome_subtype,
        )

        winner = extra_score["winner"]
        loser = extra_score["loser"]
        winning_goals = extra_score["winning_goals"]
        losing_goals = extra_score["losing_goals"]

 #   print(
 #       f"{game.game_date} "
 #       f"{game.visiting_team} at {game.home_team} "
 #       f"(game_id={game.game_id})\n"
 #       f" result_type: {outcome_subtype}\n"
 #       f" result: "
 #      + (
 #           f"{game.visiting_team} {losing_goals} at {game.home_team} {winning_goals}\n"
 #           if winner == game.home_team
 #           else f"{game.visiting_team} {winning_goals} at {game.home_team} {losing_goals}\n"
 #           if winner == game.visiting_team
 #           else "unknown\n"
 #       )
 #   )

    return {
        "winner": winner,
        "loser": loser,
        "winning_goals": winning_goals,
        "losing_goals": losing_goals,
        "outcome": outcome_subtype,
    }

def add_sim_result(sim_games, game, sim_result):
    # Map winner/loser into home/away scores
    if sim_result["winner"] == game.home_team:
        home_score = sim_result["winning_goals"]
        away_score = sim_result["losing_goals"]
    else:
        home_score = sim_result["losing_goals"]
        away_score = sim_result["winning_goals"]

    win_type = sim_result["outcome"]  # "REG", "OT", or "SO"

    sim_game = GameScore(
        game.game_id,          # game_id
        game.game_date,        # date (YYYY-MM-DD, same as in RemainingGame)
        game.visiting_team,    # away_team
        game.home_team,        # home_team
        away_score,            # away_score
        home_score,            # home_score
        win_type,              # win_type
    )

    sim_games.append(sim_game)

def print_standings(standings):
    print(
        f"{'TEAM':<4} {'DIV':<4} {'CONF':<4} "
        f"{'GP':>3} {'W':>3} {'L':>3} {'OTL':>3} "
        f"{'PTS':>4} {'RW':>3} {'ROW':>3} {'GF':>4} {'GA':>4} {'DIFF':>5}"
    )
    for t in standings:
        print(
            f"{t.team:<4} {t.division[:3]:<4} {t.conference[:3]:<4} "
            f"{t.games_played:>3} {t.wins:>3} {t.losses:>3} {t.ot_losses:>3} "
            f"{t.points:>4} {t.regulation_wins:>3} {t.row:>3} "
            f"{t.goals_for:>4} {t.goals_against:>4} {t.goal_diff:>+5}"
        )

def print_wildcard_from_standings(standings_rows):
    wc = wildcard_standings(standings_rows)

    east = wc["East"]
    west = wc["West"]

    east_divisions = sorted(east["division_spots"].keys())
    west_divisions = sorted(west["division_spots"].keys())

    print("NHL WILDCARD STANDINGS\n")

    # EAST
    print("=== EASTERN CONFERENCE ===\n")

    for division in east_divisions:
        print(f"{division.upper()} DIVISION")
        for idx, team in enumerate(east["division_spots"][division], start=1):
            print(_format_team_line(team, idx))
        print()

    print("EASTERN CONFERENCE WILD CARD")
    for idx, team in enumerate(east["wildcards"], start=1):
        print(_format_team_line(team, idx))
    print()

    if east["outside"]:
        print("EASTERN CONFERENCE OUTSIDE")
        for team in east["outside"]:
            print(_format_team_line(team))
        print()

    # WEST
    print("=== WESTERN CONFERENCE ===\n")

    for division in west_divisions:
        print(f"{division.upper()} DIVISION")
        for idx, team in enumerate(west["division_spots"][division], start=1):
            print(_format_team_line(team, idx))
        print()

    print("WESTERN CONFERENCE WILD CARD")
    for idx, team in enumerate(west["wildcards"], start=1):
        print(_format_team_line(team, idx))
    print()

    if west["outside"]:
        print("WESTERN CONFERENCE OUTSIDE")
        for team in west["outside"]:
            print(_format_team_line(team))
        print()

def sim_end_of_season(past_games,new_games):
    #past_games = get_season_game_scores(season)
    #new_games = all_remaining_games(season)

    sim_games = list(past_games)
    reg_ot_so_stats = reg_ot_so(past_games)
    goal_histograms = build_goal_histograms_from_games(past_games)

 #   standings = standings_from_game_scores(past_games)
 #   print_wildcard_from_standings(standings)

    for game in new_games:
        sim_result = sim_game_result(
            game,
            reg_ot_so_stats,
            goal_histograms,
        )

        add_sim_result(sim_games, game, sim_result)

 #   projected_standings = standings_from_game_scores(sim_games)
 #   print("\n=== PROJECTED WILDCARD STANDINGS (AFTER SIM) ===")
 #   print_wildcard_from_standings(projected_standings)

    return sim_games

def wildcard_spot_from_games(games, team):
    team = validate_team_code(team)
    standings = standings_from_game_scores(games)
    wc = wildcard_standings(standings)

    division = TEAM_TO_DIVISION[team]
    conference = DIVISION_TO_CONFERENCE[division]
    conf = wc[conference]

    # Division spots: 1, 2, 3
    for division_name, rows in conf["division_spots"].items():
        for index, row in enumerate(rows, start=1):
            if row["team"] == team:
                return str(index)

    # Wild cards: W1, W2
    for index, row in enumerate(conf["wildcards"], start=1):
        if row["team"] == team:
            return f"W{index}"

    # Outside playoffs: 9-16 within conference
    outside_rows = conf["outside"]
    for index, row in enumerate(outside_rows, start=9):
        if row["team"] == team:
            return str(index)

    return "unknown"

def margin_of_error_95(num_iterations: int) -> float:
    if num_iterations <= 0:
        raise ValueError("num_iterations must be positive")

    return 98.0 / (num_iterations ** 0.5)

def sorted_playoff_odds_results(team_counters):
    results = []

    for team_code in TEAM_TO_DIVISION:
        counter_in = team_counters[team_code]["in"]
        counter_out = team_counters[team_code]["out"]
        total = counter_in + counter_out
        percent_in = (counter_in / total) * 100 if total else 0.0

        results.append({
            "team": team_code,
            "in": counter_in,
            "out": counter_out,
            "total": total,
            "percent_in": percent_in,
        })

    return sorted(results, key=lambda row: (-row["percent_in"], row["team"]))

def sorted_playoff_odds_results_by_conference(team_counters):
    east_results = []
    west_results = []

    for team_code in TEAM_TO_DIVISION:
        division = TEAM_TO_DIVISION[team_code]
        conference = DIVISION_TO_CONFERENCE[division]

        counter_in = team_counters[team_code]["in"]
        counter_out = team_counters[team_code]["out"]
        total = counter_in + counter_out
        percent_in = (counter_in / total) * 100 if total else 0.0

        row = {
            "team": team_code,
            "division": division,
            "conference": conference,
            "in": counter_in,
            "out": counter_out,
            "total": total,
            "percent_in": percent_in,
        }

        if conference == "East":
            east_results.append(row)
        else:
            west_results.append(row)

    east_results = sorted(east_results, key=lambda row: (-row["percent_in"], row["team"]))
    west_results = sorted(west_results, key=lambda row: (-row["percent_in"], row["team"]))

    return {
        "East": east_results,
        "West": west_results,
    }

def print_playoff_odds_by_conference(results_by_conference, moe: float):
    print("EASTERN CONFERENCE")
    for index, row in enumerate(results_by_conference["East"], start=1):
        print(
            f"{index:>2}. {row['team']} playoff chances = "
            f"{row['percent_in']:.1f}% ± {moe:.1f}%"
        )

    print("\nWESTERN CONFERENCE")
    for index, row in enumerate(results_by_conference["West"], start=1):
        print(
            f"{index:>2}. {row['team']} playoff chances = "
            f"{row['percent_in']:.1f}% ± {moe:.1f}%"
        )

def print_playoff_odds_by_wildcard(results_by_conference, moe: float, num_sims: int, projected_presidents_team: str | None):
    def simple_status_for_team(
        row: dict,
        *,
        division_rank: int | None,
        conference_rank: int | None,
        presidents_team: str | None,
    ) -> str | None:
        pct = row["percent_in"]
        team = row["team"]

        if pct <= 0.05:
            return "Eliminated"

        if pct < 99.95:
            return None

        if presidents_team and team == presidents_team:
            return "Presidents Trophy"
        if conference_rank == 1:
            return "clinched conference"
        if division_rank == 1:
            return "clinched division"
        return "Clinched"
    def format_odds_line(row: dict, rank=None, status=None) -> str:
        rank_text = f"{rank:>2}. " if rank is not None else " "

        if status:
            # Example: " 1. BUF Clinched Atlantic"
            return f"{rank_text}{row['team']:<4} {status} {row['division']}"

        # Default to percentage text
        pct = row["percent_in"]
        if abs(pct - 100.0) < 0.05:
            pct_text = "100"
        elif abs(pct - 0.0) < 0.05:
            pct_text = "0"
        else:
            pct_text = f"{pct:>5.1f}"

        return f"{rank_text}{row['team']:<4} {pct_text}% {row['division']}"

    # Build global ranking across both conferences
    all_rows = results_by_conference["East"] + results_by_conference["West"]
    global_sorted = sorted(all_rows, key=lambda r: (-r["percent_in"], r["team"]))
    global_rank_map = {row["team"]: i + 1 for i, row in enumerate(global_sorted)}

    def print_conference(conference_name: str, rows: list, global_rank_map: dict[str, int]):
        print("=" * 48)
        print(f"{conference_name.upper()}ERN CONFERENCE")
        print("=" * 48)

        divisions = {}
        for row in rows:
            divisions.setdefault(row["division"], []).append(row)

        sorted_divisions = {
            division: sorted(rows, key=lambda r: (-r["percent_in"], r["team"]))
            for division, rows in divisions.items()
        }

        division_names = sorted(sorted_divisions.keys())
        automatic_qualifiers = []

        # Division ranks per team
        division_rank_map: dict[str, int] = {}
        for division in division_names:
            for i, row in enumerate(sorted_divisions[division], start=1):
                division_rank_map[row["team"]] = i

        conference_rank_map = {}
        # Rank within conference by odds
        conference_sorted = sorted(rows, key=lambda r: (-r["percent_in"], r["team"]))
        for i, row in enumerate(conference_sorted, start=1):
            conference_rank_map[row["team"]] = i

        automatic_qualifiers = []
        division_names = sorted(sorted_divisions.keys())

        for division in division_names:
            top_three = sorted_divisions[division][:3]
            print(f"{division.upper()} DIVISION")
            for index, row in enumerate(top_three, start=1):
                team = row["team"]
                status = simple_status_for_team(
                    row,
                    division_rank=division_rank_map.get(team),
                    conference_rank=conference_rank_map.get(team),
                    presidents_team=projected_presidents_team,
                )
                print(format_odds_line(row, index, status=status))
            print()
            automatic_qualifiers.extend(top_three)

        auto_teams = {row["team"] for row in automatic_qualifiers}
        remaining = [row for row in rows if row["team"] not in auto_teams]
        remaining_sorted = sorted(remaining, key=lambda r: (-r["percent_in"], r["team"]))

        wildcards = remaining_sorted[:2]
        outside = remaining_sorted[2:]

        print(f"{conference_name.upper()}ERN CONFERENCE WILD CARD")
        for index, row in enumerate(wildcards, start=1):
            team = row["team"]
            status = simple_status_for_team(
                row,
                division_rank=division_rank_map.get(team),
                conference_rank=conference_rank_map.get(team),
                presidents_team=projected_presidents_team,
            )
            print(format_odds_line(row, index, status=status))
        print()

        if outside:
            print(f"{conference_name.upper()}ERN CONFERENCE OUTSIDE")
            print("=" * 48)
            for row in outside:
                team = row["team"]
                status = simple_status_for_team(
                    row,
                    division_rank=division_rank_map.get(team),
                    conference_rank=conference_rank_map.get(team),
                    presidents_team=projected_presidents_team,
                )
                print(format_odds_line(row, status=status))
            print()

    today = datetime.now().strftime("%A, %B %d, %Y %H:%M:%S")
    print("=" * 48)
    print(today)
    print("-" * 48)
    print("PLAYOFF ODDS AS WILDCARD STANDINGS")
    print(f"Margin of error (95%): ± {moe:.1f} percentage points")
    print("=" * 48)
    print()

    print_conference("East", results_by_conference["East"], global_rank_map)
    print_conference("West", results_by_conference["West"], global_rank_map)

def expected_regular_season_games(season: str) -> int:
    start_year = int(season[:4])
    if start_year >= 2026:
        return (32 * 84) // 2
    return (32 * 82) // 2


def is_regular_season_in_progress(season: str) -> bool:
    completed_games = get_season_game_scores(season)
    return len(completed_games) < expected_regular_season_games(season)

#python3 -c 'import nhltools.playoff_odds as po; po.playoff_odds("20252026",16000)'
def playoff_odds(season: str,num_sims: int):
    start_time = perf_counter()

    past_games = get_season_game_scores(season)
    new_games = all_remaining_games(season)

    today = datetime.now().strftime("%A, %B %d, %Y %H:%M:%S")
    print(f"\n=== STANDINGS - {today} ===")
    standings = standings_from_game_scores(past_games)
    print_wildcard_from_standings(standings)

    elapsed = perf_counter() - start_time
    print(f"\nTime taken to fetch API data: {elapsed:.3f} seconds")

    team_counters = {
       team_code: {"in": 0, "out": 0}
        for team_code in TEAM_TO_DIVISION
    }

    # New: track projected points across simulations
    projected_points_totals = {
        team_code: 0
        for team_code in TEAM_TO_DIVISION
    }
    # Optional: track how often each team finishes overall #1
    projected_overall_1_finishes = {
        team_code: 0
        for team_code in TEAM_TO_DIVISION
    }

    if is_regular_season_in_progress(season):

        moe = margin_of_error_95(num_sims)

        for _ in range(num_sims):
            sim_games = sim_end_of_season(past_games, new_games)
            standings = standings_from_game_scores(sim_games)

            # standings is already sorted with your tie-breakers (_standings_sort_key)
            # 1) accumulate projected points
            for team in standings:
                projected_points_totals[team.team] += team.points

            # 2) track projected overall #1 finishes
            if standings:
                projected_overall_1_finishes[standings[0].team] += 1

            wc = wildcard_standings(standings)

            playoff_teams = set()

            for conference in wc.values():
                for division_rows in conference["division_spots"].values():
                    for row in division_rows:
                        playoff_teams.add(row["team"])

                for row in conference["wildcards"]:
                    playoff_teams.add(row["team"])

            for team_code in TEAM_TO_DIVISION:
                if team_code in playoff_teams:
                    team_counters[team_code]["in"] += 1
                else:
                    team_counters[team_code]["out"] += 1
        
        # Compute average projected points per team (for later use)
        avg_projected_points = {}
        if num_sims > 0:
            for team_code in TEAM_TO_DIVISION:
                avg_projected_points[team_code] = projected_points_totals[team_code] / num_sims
        
            # Pick projected Presidents Trophy based on highest avg projected points
            projected_presidents_team = max(
                avg_projected_points.items(),
                key=lambda item: (item[1], item[0]),
            )[0]
        else:
            projected_presidents_team = None

        results = sorted_playoff_odds_results(team_counters)
        results_by_conference = sorted_playoff_odds_results_by_conference(team_counters)
        # print_playoff_odds_by_conference(results_by_conference, moe)
        print_playoff_odds_by_wildcard(results_by_conference, moe, num_sims, projected_presidents_team)

        print_first_round_matchups_from_odds(results_by_conference)

    else:
        print("Regular season is over no simulation was run")



    elapsed = perf_counter() - start_time
    print(f"\nElapsed time: {elapsed:.3f} seconds")

def remaining_games_for_team_in_order(new_games, team: str):
    team = validate_team_code(team)

    team_games = [
        g for g in new_games
        if g.home_team == team or g.visiting_team == team
    ]

    team_games.sort(key=lambda g: (g.game_date, g.game_id))
    return team_games

def sim_teams_next_game_odds(season, past_games, new_games, team, num_sims):
    team = validate_team_code(team)

    game_counter=0
    new_games = all_remaining_games(season)
    for game in remaining_games_for_team_in_order(new_games, team):
        print(
            f"{game.game_date} "
            f"{game.visiting_team} at {game.home_team} "
            f"(game_id={game.game_id} ({game_counter}))"
        )
        game_counter = game_counter+1

def simulate_season_with_synthetic_result(
    synthetic_game: GameScore,
    past_games,
    new_games,
    num_sims: int,
):
    # 1) Apply the synthetic game
    past_with_synthetic = list(past_games)
    past_with_synthetic.append(synthetic_game)

    # 2) Remove that game from remaining schedule (by game_id)
    remaining_after_synthetic = [
        g for g in new_games if g.game_id != synthetic_game.game_id
    ]

    # 3) Run usual MC loop
    team_counters = {
        team_code: {"in": 0, "out": 0}
        for team_code in TEAM_TO_DIVISION
    }

    moe = margin_of_error_95(num_sims)

    for _ in range(num_sims):
        sim_games = sim_end_of_season(past_with_synthetic, remaining_after_synthetic)
        standings = standings_from_game_scores(sim_games)
        wc = wildcard_standings(standings)

        playoff_teams = set()
        for conference in wc.values():
            for division_rows in conference["division_spots"].values():
                for row in division_rows:
                    playoff_teams.add(row["team"])
            for row in conference["wildcards"]:
                playoff_teams.add(row["team"])

        for team_code in TEAM_TO_DIVISION:
            if team_code in playoff_teams:
                team_counters[team_code]["in"] += 1
            else:
                team_counters[team_code]["out"] += 1

    results_by_conference = sorted_playoff_odds_results_by_conference(team_counters)
    print_playoff_odds_by_wildcard(results_by_conference, moe, num_sims)

    return team_counters

def simulate_next_game_score_scenario(season: str, team: str, num_sims: int, team_score: int, oponent_score: int, result_type: str):
 
    result_type = result_type.upper()
    if result_type not in {"REG", "OT", "SO"}:
        raise ValueError("result_type must be 'REG', 'OT', or 'SO'")
 
    team = validate_team_code(team)
    past_games = get_season_game_scores(season)
    new_games = all_remaining_games(season)

    # Find that team's next game
    team_games = [
        g for g in new_games
        if g.home_team == team or g.visiting_team == team
    ]
    if not team_games:
        print(f"No remaining regular-season games for {team}")
        return

    next_game = min(team_games, key=lambda g: (g.game_date, g.game_id))

    if next_game.home_team == team:
        # Team is home
        home_score = team_score
        away_score = oponent_score
    else:
        # Team is away
        home_score = oponent_score
        away_score = team_score

    synthetic = GameScore(
        next_game.game_id,
        next_game.game_date,
        next_game.visiting_team,
        next_game.home_team,
        away_score,
        home_score,
        result_type,  # REG / OT / SO
    )

    print(
        f"Assuming synthetic game: {synthetic.date} "
        f"{synthetic.away_team} {synthetic.away_score} at "
        f"{synthetic.home_team} {synthetic.home_score} {result_type}"
    )

    return simulate_season_with_synthetic_result(
        synthetic_game=synthetic,
        past_games=past_games,
        new_games=new_games,
        num_sims=num_sims,
    )

# python3 -c 'import nhltools.playoff_odds as po; po.next_game_playoff_odds("20252026",8000,"OTT",3,4,"REG")'
def next_game_playoff_odds(season: str,num_sims: int,team: str,team_score: int,oponent_score: int,result_type: str):
    start_time = perf_counter()
    past_games = get_season_game_scores(season)
    new_games = all_remaining_games(season)  

    if is_regular_season_in_progress(season):
        #team_score = 3
        #oponent_score = 2
        simulate_next_game_score_scenario(season, team, num_sims, team_score, oponent_score, result_type)
    else:
        print("Regular season is over no simulation was run")

    elapsed = perf_counter() - start_time
    print(f"\nElapsed time: {elapsed:.3f} seconds")