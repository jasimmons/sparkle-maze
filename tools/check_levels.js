// Checks every hand-made level in web/game.html:
//  1. Pip can reach the rainbow door (same rules as the game).
//  2. Every star can be collected.
//  3. Every locked door and gate is really needed (the level can't be beaten without it).
// Run: node tools/check_levels.js
const fs = require("fs");
const path = require("path");

const html = fs.readFileSync(path.join(__dirname, "..", "web", "game.html"), "utf8");
const src = html.split("/*LEVELS-START*/")[1].split("/*LEVELS-END*/")[0];
const LEVELS = new Function(src + "; return LEVELS;")();

const DIRS = [[1, 0], [-1, 0], [0, 1], [0, -1]];

function solve(map, goal) {
  const H = map.length, W = map[0].length;
  const T = (x, y) => (map[y] && map[y][x]) || "#";
  let start, blocks = [], pads = [], itemsList = [];
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const c = map[y][x];
    if (c === "P") start = [x, y];
    if (c === "H") blocks.push(x + "," + y);
    if (c === "o") pads.push(x + "," + y);
    if ("*abc".includes(c)) itemsList.push(x + "," + y);
  }
  const terr = (x, y) => { const c = T(x, y); return "P*abcH".includes(c) ? "." : c; };
  const init = { x: start[0], y: start[1], blocks: blocks.sort(), got: 0, open: [], gate: pads.length === 0 };
  const keyOf = (s) => [s.x, s.y, s.blocks.join(";"), s.got, s.open.sort().join(";"), s.gate].join("|");
  const seen = new Set([keyOf(init)]);
  const q = [init];
  while (q.length) {
    const s = q.shift();
    if (goal(s, terr, itemsList)) return true;
    const keys = new Set(itemsList.filter((k, i) => (s.got >> i) & 1).map((k) => { const [x, y] = k.split(",").map(Number); return T(x, y); }));
    for (const [dx, dy] of DIRS) {
      const nx = s.x + dx, ny = s.y + dy, nk = nx + "," + ny, t = terr(nx, ny);
      if (t === "#") continue;
      if (t === "G" && !s.gate) continue;
      const open = [...s.open];
      if ("ABC".includes(t) && !open.includes(nk)) { if (!keys.has(t.toLowerCase())) continue; open.push(nk); }
      let blocksN = s.blocks, gate = s.gate;
      if (s.blocks.includes(nk)) {
        const bx = nx + dx, by = ny + dy, bk = bx + "," + by, bt = terr(bx, by);
        const itemThere = itemsList.some((k, i) => k === bk && !((s.got >> i) & 1));
        if (bt === "#" || bt === "E" || ("ABC".includes(bt) && !open.includes(bk)) || (bt === "G" && !gate) || s.blocks.includes(bk) || itemThere) continue;
        blocksN = s.blocks.map((b) => (b === nk ? bk : b)).sort();
        if (!gate && pads.every((p) => blocksN.includes(p))) gate = true;
      }
      let got = s.got;
      const idx = itemsList.indexOf(nk);
      if (idx >= 0) got |= 1 << idx;
      const ns = { x: nx, y: ny, blocks: blocksN, got, open, gate };
      if (t === "E") { if (goal(ns, terr, itemsList)) return true; continue; }
      const k = keyOf(ns);
      if (!seen.has(k)) { seen.add(k); q.push(ns); }
    }
  }
  return false;
}

const reachExit = (s, terr) => terr(s.x, s.y) === "E";
let ok = true;
LEVELS.forEach((L, i) => {
  const errs = [];
  const H = L.map.length, W = L.map[0].length;
  if (!L.map.every((r) => r.length === W)) errs.push("rows have different lengths");
  if (!solve(L.map, reachExit)) errs.push("rainbow door can't be reached");
  // each star collectable (on the way to a finish isn't required; just reachable)
  L.map.forEach((row, y) => [...row].forEach((c, x) => {
    if (c !== "*") return;
    if (!solve(L.map, (s, terr, items) => { const i = items.indexOf(x + "," + y); return (s.got >> i) & 1; })) errs.push(`star at ${x},${y} can't be reached`);
    if ("ABCG".includes(c)) return;
  }));
  // each door / gate must matter
  L.map.forEach((row, y) => [...row].forEach((c, x) => {
    if (!"ABCG".includes(c)) return;
    const walled = L.map.map((r, yy) => (yy === y ? r.slice(0, x) + "#" + r.slice(x + 1) : r));
    if (solve(walled, reachExit)) errs.push(`${c} at ${x},${y} isn't needed`);
  }));
  const stars = L.map.join("").split("*").length - 1;
  console.log(`${errs.length ? "FAIL" : "ok  "} ${i + 1}. ${L.name} (${W}x${H}, ${stars} stars)${errs.length ? " -> " + errs.join("; ") : ""}`);
  if (errs.length) ok = false;
});
process.exit(ok ? 0 : 1);
