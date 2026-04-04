from datetime import datetime

from nhltools.schedule_by_day import fetch_schedule_by_day, format_schedule_by_day


def usage():
    print("USAGE: nhl todays-games")
    print("Example:")
    print(" nhl todays-games")


def get_today_date():
    return datetime.now().astimezone().strftime("%Y-%m-%d")


def main(argv=None):
    if argv is None:
        argv = []

    if len(argv) != 0:
        usage()
        raise SystemExit(1)

    game_date = get_today_date()
    games = fetch_schedule_by_day(game_date)
    print(format_schedule_by_day(game_date, games))


if __name__ == "__main__":
    main()
