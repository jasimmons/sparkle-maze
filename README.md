# Pip's Sparkle Maze

A cozy maze and puzzle game for kids aged 5 to 8. Kids pick a friend to play
(Pip the bunny, Lolo the axolotl or Luna the unicorn), explore six hand-made
mazes, then a "surprise maze" that is new every time.

## Play it

    python3 server.py        # then open http://localhost:8000

No installs needed: the server uses only the Python standard library. The whole
game runs in the browser from `web/game.html`.

## Controls

- Arrow keys or WASD, the on-screen arrows, a swipe, or tap a tile to walk there
- Undo (Z or Backspace) and Restart (R)
- The microphone button reads the level hint out loud for kids who don't read yet

## Puzzle pieces

| Map letter | What it is |
|---|---|
| `P` | Pip's starting spot |
| `E` | Rainbow door (the goal) |
| `*` | Star to collect |
| `a` `b` `c` / `A` `B` `C` | Pink, purple and mint keys and their doors |
| `H` / `o` / `G` | Heart box, heart spot, and the gate the spots open |

Levels live between `/*LEVELS-START*/` and `/*LEVELS-END*/` in `web/game.html`.
After editing one, run `node tools/check_levels.js` to make sure every level can
still be finished, every star can be reached, and every door and gate matters.
