from datetime import date, datetime
from nhlpy import NHLClient

def print_todays_games():
    client = NHLClient()
    games = client.schedule.daily_schedule()

    today = date.today()
    today2 = today.strftime("%b. %d, %Y").replace(". 0", ". ")
    print(f"Today's NHL games ({today2}):")

    for game in games.get("games", []):
        away = game["awayTeam"]["abbrev"]
        home = game["homeTeam"]["abbrev"]
        start_utc = datetime.fromisoformat(game["startTimeUTC"].replace("Z", "+00:00"))
        start_local = start_utc.astimezone()
        print(f"{away} @ {home}  {start_local:%-I:%M %p}")

def main():
    print_todays_games()

main()
