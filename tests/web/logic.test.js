import { test } from "node:test";
import assert from "node:assert/strict";
import {
  acceptCandidate, buildRows, candidateList, dismissRepo, filterRows,
  isRecent, relativeTime, removePort, setFollow, slugify, sortRows, undismissRepo,
} from "../../web/logic.js";

const PORTS = [
  { id: "bloodborne", game: "Bloodborne", repo: "Supermedo/bloodborne_pc", os: "Windows", status: "play", reach: "", note: "n1" },
  { id: "uo", game: "Unicorn Overlord", repo: "hachi23/uo", os: "Linux", status: "early", reach: "Cap. 1", note: "" },
];
const GITHUB = {
  repos: {
    "supermedo/bloodborne_pc": { stars: 3700, pushed_at: "2026-10-18T11:00:00Z", release_tag: "v1", release_date: "2026-10-17",
      archived: false, fork: false, missing: false, renamed_to: null, status_text: "playable", status_changed_at: "2026-10-16" },
  },
};
const NOW = new Date("2026-10-18T12:00:00Z");

test("buildRows merges manual and automatic data and marks follows", () => {
  const rows = buildRows(PORTS, GITHUB, ["uo"]);

  assert.equal(rows.length, 2);
  assert.equal(rows[0].stars, 3700);
  assert.equal(rows[0].statusText, "playable");
  assert.equal(rows[0].url, "https://github.com/Supermedo/bloodborne_pc");
  assert.equal(rows[0].followed, false);
  assert.equal(rows[1].followed, true);
  assert.equal(rows[1].stars, null);
  assert.equal(rows[1].missing, false);
  assert.equal(rows[0].forkOf, null);
});

test("buildRows exposes the fork parent", () => {
  const github = { repos: { "a/b": { ...GITHUB.repos["supermedo/bloodborne_pc"], fork: true, fork_of: "c/origin" } } };

  const [row] = buildRows([{ ...PORTS[0], repo: "a/b" }], github, []);

  assert.equal(row.fork, true);
  assert.equal(row.forkOf, "c/origin");
});

test("buildRows points the link to the renamed repo", () => {
  const github = { repos: { "a/old": { ...GITHUB.repos["supermedo/bloodborne_pc"], renamed_to: "a/new" } } };

  const [row] = buildRows([{ ...PORTS[0], repo: "a/old" }], github, []);

  assert.equal(row.url, "https://github.com/a/new");
});

test("filterRows by tab and case-insensitive query on game and repo", () => {
  const rows = buildRows(PORTS, GITHUB, ["uo"]);

  assert.deepEqual(filterRows(rows, { tab: "following", query: "" }).map(r => r.id), ["uo"]);
  assert.deepEqual(filterRows(rows, { tab: "all", query: "SUPERMEDO" }).map(r => r.id), ["bloodborne"]);
  assert.deepEqual(filterRows(rows, { tab: "all", query: "  " }).length, 2);
});

test("sortRows sorts without mutating and puts empty values last", () => {
  const rows = buildRows(PORTS, GITHUB, []);
  const original = rows.map(r => r.id);

  assert.deepEqual(sortRows(rows, "stars", -1).map(r => r.id), ["bloodborne", "uo"]);
  assert.deepEqual(sortRows(rows, "stars", 1).map(r => r.id), ["bloodborne", "uo"]);
  assert.deepEqual(sortRows(rows, "game", -1).map(r => r.id), ["uo", "bloodborne"]);
  assert.deepEqual(sortRows(rows, "status", -1).map(r => r.id), ["bloodborne", "uo"]);
  assert.deepEqual(rows.map(r => r.id), original);
});

test("relativeTime in Spanish", () => {
  assert.equal(relativeTime("2026-10-18T11:50:00Z", NOW), "hace minutos");
  assert.equal(relativeTime("2026-10-18T07:00:00Z", NOW), "hace 5 h");
  assert.equal(relativeTime("2026-10-17T10:00:00Z", NOW), "hace 1 día");
  assert.equal(relativeTime("2026-10-10T12:00:00Z", NOW), "hace 8 días");
  assert.equal(relativeTime(null, NOW), "—");
});

test("isRecent within N days", () => {
  assert.equal(isRecent("2026-10-12", NOW, 7), true);
  assert.equal(isRecent("2026-10-10", NOW, 7), false);
  assert.equal(isRecent(null, NOW, 7), false);
});

test("candidateList hides known and dismissed repos and sorts by stars", () => {
  const candidates = { candidates: {
    "x/low": { repo: "x/low", stars: 1 }, "x/high": { repo: "x/high", stars: 50 },
    "hachi23/uo": { repo: "hachi23/uo", stars: 3 }, "x/gone": { repo: "X/Gone", stars: 9 },
  } };

  const list = candidateList(candidates, PORTS, { dismissed: ["x/gone"] });

  assert.deepEqual(list.map(c => c.repo), ["x/high", "x/low"]);
});

test("dismissRepo adds once without mutating", () => {
  const review = { dismissed: ["a/b"] };

  assert.deepEqual(dismissRepo(review, "c/d"), { dismissed: ["a/b", "c/d"] });
  assert.deepEqual(dismissRepo(review, "A/B"), review);
  assert.deepEqual(review, { dismissed: ["a/b"] });
});

test("slugify builds kebab-case ids", () => {
  assert.equal(slugify("ShadowOfTheColossus-PC"), "shadowofthecolossus-pc");
  assert.equal(slugify("The_Order 1886!!"), "the-order-1886");
  assert.equal(slugify("___"), "port");
});

test("acceptCandidate appends a new early-status port with a unique id", () => {
  const ports = { ports: [{ ...PORTS[0], id: "driveclub-port" }] };
  const candidate = { repo: "BlackLine/Driveclub-Port", description: "Driveclub PS4 PC Port" };

  const result = acceptCandidate(ports, candidate);

  assert.equal(result.ports.length, 2);
  assert.deepEqual(result.ports[1], {
    id: "driveclub-port-2", game: "Driveclub-Port", repo: "BlackLine/Driveclub-Port",
    os: "", status: "early", reach: "", note: "",
  });
  assert.equal(ports.ports.length, 1);
});

test("acceptCandidate ignores repos already present", () => {
  const ports = { ports: PORTS };

  assert.equal(acceptCandidate(ports, { repo: "SUPERMEDO/bloodborne_pc", description: "" }), ports);
});

test("setFollow is idempotent in both directions", () => {
  assert.deepEqual(setFollow(["a"], "a", true), ["a"]);
  assert.deepEqual(setFollow(["a"], "b", true), ["a", "b"]);
  assert.deepEqual(setFollow(["a"], "a", false), []);
  assert.deepEqual(setFollow([], "a", false), []);
  const follows = ["a"];
  setFollow(follows, "b", true);
  assert.deepEqual(follows, ["a"]);
});

test("removePort and undismissRepo undo accept and dismiss", () => {
  const ports = { ports: [PORTS[0]] };
  const accepted = acceptCandidate(ports, { repo: "x/new", description: "" });

  assert.deepEqual(removePort(accepted, "X/New"), ports);
  assert.deepEqual(undismissRepo({ dismissed: ["a/b", "c/d"] }, "C/D"), { dismissed: ["a/b"] });
});

test("buildRows flags a replaced repo", () => {
  const github = { repos: { "a/b": { ...GITHUB.repos["supermedo/bloodborne_pc"], replaced: true } } };

  assert.equal(buildRows([{ ...PORTS[0], repo: "a/b" }], github, [])[0].replaced, true);
});
