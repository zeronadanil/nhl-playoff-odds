import subprocess
import sys
from pathlib import Path

from nhltools.current_standings import main as current_standings_main
from nhltools.daily_scores import main as daily_scores_main
from nhltools.stats_w_l_ot import main as stats_w_l_ot_main
from nhltools.remaining_games import main as remaining_games_main
from nhltools.schedule_by_day import main as schedule_by_day_main
from nhltools.season_results_by_team import main as season_results_by_team_main
from nhltools.todays_games import main as todays_games_main

ROOT = Path(__file__).resolve().parent.parent

DIRECT_COMMANDS = {
    "current-standings": current_standings_main,
    "daily-scores": daily_scores_main,
    "stats-w-l-ot": stats_w_l_ot_main,
    "remaining-games": remaining_games_main,
    "schedule-by-day": schedule_by_day_main,
    "season-results-by-team": season_results_by_team_main,
    "todays-games": todays_games_main,
}

SCRIPT_COMMANDS = {
    "today": "nhl-todays-games.py",
    "schedule-day": "nhl-schedule-by-day.py",
    "scores": "nhl-daily-scores.py",
    "season-results": "nhl-season-results-by-team.py",
    "remaining": "nhl-remaining-games-by-team.py",
}


def print_help():
    print("Usage: nhl <command> [args]")
    print("")
    print("Commands:")
    for name in sorted({*DIRECT_COMMANDS.keys(), *SCRIPT_COMMANDS.keys()}):
        print(f"  {name}")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help"}:
        print_help()
        raise SystemExit(0)

    cmd = sys.argv[1]

    if cmd in DIRECT_COMMANDS:
        DIRECT_COMMANDS[cmd](sys.argv[2:])
        return

    script = SCRIPT_COMMANDS.get(cmd)
    if script is None:
        print(f"Unknown command: {cmd}")
        print("")
        print_help()
        raise SystemExit(1)

    subprocess.run([sys.executable, str(ROOT / script), *sys.argv[2:]], check=True)


if __name__ == "__main__":
    main()
