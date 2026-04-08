# nhltools

A starter Python CLI library that unifies several NHL helper scripts under one command.

## Install

```bash
pip install -e .
```

## Commands

```bash
python3 -c 'import nhltools.playoff_odds as po; po.playoff_odds("20252026",16000)
nhl today
nhl schedule-day 2026-04-03
nhl scores-day 2026-04-03
nhl standings wildcard
nhl standings division
nhl standings conference
nhl standings league
nhl results 20252026 OTT
nhl remaining 20252026 OTT
nhl stats 20252026 OTT
nhl stats 20252026 ALL
```
