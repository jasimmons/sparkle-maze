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

## Surprise maze

The dice button makes a new random maze (Small 13x11 or Big 25x21) with one
treasure chest. Opening it rolls a die: 1-3 finds that many stars, 4 is a
tornado that carries you somewhere new, 5 is a sleepy ghost that takes your
stars, and 6 is a trap door to a brand new maze (you keep stars and keys).

Every level has a timer that starts on the first step, and the game remembers
your best time for each level (and for each surprise maze size).

## Puzzle pieces

| Map letter | What it is |
|---|---|
| `P` | Pip's starting spot |
| `E` | Rainbow door (the goal) |
| `*` | Star to collect |
| `a` `b` `c` / `A` `B` `C` | Pink, purple and mint keys and their doors |
| `H` / `o` / `G` | Heart box, heart spot, and the gate the spots open |
| `T` | Treasure chest: rolls a die for 1-3 stars, a tornado, a ghost or a trap door |

Levels live between `/*LEVELS-START*/` and `/*LEVELS-END*/` in `web/game.html`.
After editing one, run `node tools/check_levels.js` to make sure every level can
still be finished, every star can be reached, and every door and gate matters.
