#!/usr/bin/env python3

import sys

from nhltools.stats_w_l_ot import (
    TEAM_CODES,
    format_league_stats,
    format_team_stats,
    get_league_stats,
    get_team_stats,
)


def usage():
    print("USAGE: nhl-lib-stats-w-l-ot.py YYYYYYYY TEAM")
    print("Examples:")
    print(" nhl-lib-stats-w-l-ot.py 20252026 OTT")
    print(" nhl-lib-stats-w-l-ot.py 20252026 all")
    print(' nhl-lib-stats-w-l-ot.py 20252026 "all teams"')


def main():
    if len(sys.argv) != 3:
        usage()
        sys.exit(1)

    season = sys.argv[1]
    team = sys.argv[2].strip()

    if len(season) != 8 or not season.isdigit():
        usage()
        sys.exit(1)

    if team.lower() in {"all", "all teams"}:
        stats = get_league_stats(season)
        print(format_league_stats(season, stats))
        return

    team_code = team.upper()
    if team_code not in TEAM_CODES:
        print(f"Unknown team code: {team}")
        usage()
        sys.exit(1)

    stats = get_team_stats(season, team_code)
    print(format_team_stats(team_code, season, stats))


if __name__ == "__main__":
    main()
