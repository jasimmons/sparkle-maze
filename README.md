# Pip's Sparkle Maze

A cozy maze and puzzle game for kids aged 5 to 8. Kids pick a friend to play
(Pip the bunny, Lolo the axolotl or Luna the unicorn), explore six hand-made
mazes, then a "surprise maze" that is new every time.

## Play it

    python3 server.py        # then open http://localhost:8000

No installs needed: this server uses only the Python standard library (accounts
need the docker compose setup below). The whole
game runs in the browser from `web/game.html`, which loads its levels from
`web/levels/` when it starts (so opening the HTML file straight from disk won't
work; use the server).

## Play it with accounts (docker compose)

The backend in `backend/` (FastAPI) serves the same game plus an API that saves, per
signed-in player, a high score for every maze (most stars, then fastest time) and the
total number of stars they've ever found. Data lives in a MySQL container.

1. `cp .env.example .env` and fill it in:
   - `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD`: any long random strings.
   - `SESSION_SECRET`: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
   - GitHub sign-in: go to https://github.com/settings/developers, **New OAuth App**,
     Homepage URL `http://localhost:8000`, Authorization callback URL
     `http://localhost:8000/auth/callback/github`. Copy the Client ID into
     `GITHUB_CLIENT_ID`, then **Generate a new client secret** into `GITHUB_CLIENT_SECRET`.
   - Google sign-in (optional): in https://console.cloud.google.com/apis/credentials make an
     **OAuth client ID** of type Web application with redirect URI
     `http://localhost:8000/auth/callback/google`, and fill in `GOOGLE_CLIENT_ID` and
     `GOOGLE_CLIENT_SECRET`. Each provider shows up once its two values are set.
   - `DEV_LOGIN=true` adds a "Pretend (dev)" sign-in for trying things without any OAuth
     app. Local only: anyone could sign in as anyone.
2. `docker compose up --build`, then open http://localhost:8000.

The account button sits next to the timer. Signed out, the game plays exactly as before;
signed in, every finish is saved and the button shows your star total. `.env` is
git-ignored, so keys never get committed. When this moves to a real server, set
`PUBLIC_URL` (e.g. `https://sparkle.example.com`), `COOKIE_SECURE=true`, and register
OAuth callback URLs on that address.

API: `GET /api/me`, `POST /api/finish` (`{level, stars, time_ms}`), `GET /api/scores`,
`GET /api/leaderboard/stars`, `GET /api/leaderboard/levels/{level}`. A level's id is its
file name without `.json` (or `surprise-small` / `surprise-big`). Scores come from the
browser, so a determined player could fake them; the server only checks a run doesn't
claim more stars than the maze has.

Backend tests run on SQLite, no Docker needed:

    pip install -r backend/requirements.txt pytest
    python3 -m pytest backend/tests

## Play it online

Every push to `main` publishes the game to GitHub Pages at
https://jasimmons.github.io/sparkle-maze/ (see `.github/workflows/pages.yml`).
To build the same static site yourself: `python3 server.py --build dist`.

The Claude Artifact preview is a single file that can't load `web/levels/`, so
it is published from a copy with the levels baked in:
`python3 server.py --artifact artifact.html`.

## Controls

- Arrow keys or WASD, the on-screen arrows, a swipe, or tap a tile to walk there
- Undo (Z or Backspace) and Restart (R)
- The microphone button reads the level hint out loud for kids who don't read yet

## Surprise maze

The dice button makes a new random maze (Small 13x11 or Big 25x21). A small
maze hides one treasure chest and a big one hides 2 to 5. Opening a chest rolls
a die: 1-3 finds that many stars, 4 is a tornado that carries you somewhere
new, 5 is a sleepy ghost that takes your stars, and 6 is a trap door to a
brand new maze (you keep stars and keys).

Every level has a timer that starts on the first step, and the game remembers
your best time for each level (and for each surprise maze size).

## Puzzle pieces

| Map letter | What it is |
|---|---|
| `#` / `.` | Wall and floor (the outside edge must be all walls) |
| `P` | Pip's starting spot |
| `E` | Rainbow door (the goal) |
| `*` | Star to collect |
| `a` `b` `c` / `A` `B` `C` | Pink, purple and mint keys and their doors |
| `H` / `o` / `G` | Heart box, heart spot, and the gate the spots open |
| `T` | Treasure chest: asks to open, then rolls a die for 1-3 stars (or skip it for now), a tornado, a ghost or a trap door |

## Making levels

Each hand-made level is its own file in `web/levels/`, and `web/levels/index.json`
lists them in the order they're played. A level looks like this:

```json
{
  "name": "The Pink Key",
  "fog": false,
  "hint": "The rainbow door is behind a pink door. Find the pink key!",
  "map": [
    "#############",
    "#P....#*....#",
    "..."
  ]
}
```

`{name}` in a hint becomes the friend the player picked, and `"fog": true` hides
the maze until you walk near it. To add a level, make a new file and add its name
to `index.json`. After editing levels, run `node tools/check_levels.js` to make
sure every level can still be finished, every star can be reached, and every door
and gate matters.
