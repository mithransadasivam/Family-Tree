# Groot

Groot is for the **website only**: it checks the website and the server code the website talks to. It never touches, builds or tests the Android app.

One command runs every check and prints a summary. It is safe to run as often as you like: the
server checks use a throwaway in-memory database, the website checks are pure code, and the
optional `--live` checks only read from the real site.

```
python groot/run_all.py              everything (about a minute)
python groot/run_all.py --quick      fewer random rounds (about 20 seconds)
python groot/run_all.py --live       also poke the live website (read-only)
python groot/run_all.py --no-browser skip the click-through tests
python groot/run_all.py --seed 123   replay the exact random run another run printed
```

On Windows you can also double-click `groot/groot.bat`.

## What it covers

| Group | What it does |
|---|---|
| access control | people can't reach other families' data, move people between families, link accounts they shouldn't, delete without being the owner; deleted families stay gone; relationship rules; dates |
| communities | create, join, approve, share families, search and filters, privacy of what members see |
| emails | the join-request emails and approve links (using a fake mailbox) |
| join with family | pick a family when joining a community; shared on approval |
| private details | the eye buttons: email, phone and address stay hidden unless turned on |
| random fuzz | thousands of random, often nonsensical, requests from several users, while checking that the server never errors, links never cross families / double up / loop, private values never leak, strangers stay locked out |
| website tests | the tree layout and labels, including random families shuffled in every order |
| real screens (browser) | opens the real website in a headless Edge/Chrome and clicks through it like a person: creates a dummy "Groot Test Family", adds people, edits details and eyes, joins by code, communities (join with a family, approve, search), privacy from another account's point of view, phone-sized screens, sign-out. Takes screenshots into `groot/reports/` |
| live site (`--live`) | the real site loads, both addresses match, and every private page turns anonymous visitors away |

Every random run prints its seed. If a run fails, re-run with that seed to see the same failure.

Add a new check by dropping a script in `groot/scenarios/` named `check_<something>.py`: print
`PASS ...` or `FAIL ...` lines and exit non-zero on failure (see an existing one for the setup).

## About the browser tests and the dummy tree

The browser part never touches the real site or its data. Each run builds the website from your current
code, starts a private server on this computer (127.0.0.1) with a temporary database, creates three dummy
accounts and a "Groot Test Family" through the screens, and when it finishes the server and the whole
database are deleted. The dummy family can never be seen by anyone, because it only exists on your computer
for those few seconds. Screenshots of key screens (and of any failure) are saved in `groot/reports/`,
which is not committed. It needs Node and Microsoft Edge or Google Chrome.
