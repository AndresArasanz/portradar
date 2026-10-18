import { test } from "node:test";
import assert from "node:assert/strict";
import { createStore, decodeBase64, encodeBase64 } from "../../web/store.js";

function fakeFetch(responses) {
  const calls = [];
  const fn = async (url, opts = {}) => {
    calls.push({ url, opts });
    const r = responses.shift();
    return { ok: r.status < 300, status: r.status, json: async () => r.body };
  };
  fn.calls = calls;
  return fn;
}

const file = (obj, sha) => ({ status: 200, body: { sha, content: encodeBase64(JSON.stringify(obj)) } });

test("base64 roundtrip keeps UTF-8", () => {
  const text = '{"note":"Prólogo · ñ ✅"}';

  assert.equal(decodeBase64(encodeBase64(text)), text);
  assert.equal(decodeBase64(encodeBase64(text).replace(/(.{10})/g, "$1\n")), text);
});

test("readJson fetches contents with auth header", async () => {
  const fetch = fakeFetch([file({ follows: ["a"] }, "s1")]);
  const store = createStore({ repo: "o/r", token: "tkn", fetch });

  const result = await store.readJson("data/follows.json");

  assert.deepEqual(result, { data: { follows: ["a"] }, sha: "s1" });
  assert.match(fetch.calls[0].url, /^https:\/\/api\.github\.com\/repos\/o\/r\/contents\/data\/follows\.json\?ref=main&t=\d+$/);
  assert.equal(fetch.calls[0].opts.headers.Authorization, "Bearer tkn");
});

test("updateJson reads fresh, applies the change and PUTs with sha", async () => {
  const fetch = fakeFetch([file({ follows: [] }, "s1"), { status: 200, body: {} }]);
  const store = createStore({ repo: "o/r", token: "tkn", fetch });

  const data = await store.updateJson("data/follows.json", d => ({ follows: [...d.follows, "x"] }), "seguir x");

  assert.deepEqual(data, { follows: ["x"] });
  const put = fetch.calls[1];
  assert.equal(put.opts.method, "PUT");
  const body = JSON.parse(put.opts.body);
  assert.equal(body.sha, "s1");
  assert.equal(body.message, "seguir x");
  assert.equal(body.branch, "main");
  assert.deepEqual(JSON.parse(decodeBase64(body.content)), { follows: ["x"] });
  assert.ok(decodeBase64(body.content).endsWith("\n"));
});

test("updateJson gives up after three conflicts", async () => {
  const fetch = fakeFetch([
    file({ follows: [] }, "s1"), { status: 409, body: {} },
    file({ follows: [] }, "s1"), { status: 409, body: {} },
    file({ follows: [] }, "s1"), { status: 409, body: { message: "conflict" } },
  ]);
  const store = createStore({ repo: "o/r", token: "tkn", fetch, wait: async () => {} });

  await assert.rejects(store.updateJson("data/follows.json", d => d, "m"), /409/);
  assert.equal(fetch.calls.length, 6);
});

test("updateJson retries on sha conflict", async () => {
  const fetch = fakeFetch([
    file({ follows: [] }, "s1"), { status: 409, body: {} },
    file({ follows: ["y"] }, "s2"), { status: 200, body: {} },
  ]);
  const store = createStore({ repo: "o/r", token: "tkn", fetch, wait: async () => {} });

  const data = await store.updateJson("data/follows.json", d => ({ follows: [...d.follows, "x"] }), "m");

  assert.deepEqual(data, { follows: ["y", "x"] });
  assert.equal(JSON.parse(fetch.calls[3].opts.body).sha, "s2");
});

test("updateJson throws a readable error on auth failure", async () => {
  const fetch = fakeFetch([file({ follows: [] }, "s1"), { status: 403, body: { message: "Resource not accessible" } }]);
  const store = createStore({ repo: "o/r", token: "bad", fetch });

  await assert.rejects(store.updateJson("data/follows.json", d => d, "m"), /403.*Resource not accessible/);
});

test("readJson throws on HTTP errors", async () => {
  const store = createStore({ repo: "o/r", token: "t", fetch: fakeFetch([{ status: 401, body: { message: "Bad credentials" } }]) });

  await assert.rejects(store.readJson("data/x.json"), /401/);
});

test("checkToken reports whether the token can push", async () => {
  const ok = createStore({ repo: "o/r", token: "github_pat_x", fetch: fakeFetch([{ status: 200, body: { permissions: { push: true } } }]) });
  const ro = createStore({ repo: "o/r", token: "github_pat_x", fetch: fakeFetch([{ status: 200, body: { permissions: { push: false } } }]) });
  const bad = createStore({ repo: "o/r", token: "github_pat_x", fetch: fakeFetch([{ status: 401, body: {} }]) });

  assert.equal(await ok.checkToken(), true);
  assert.equal(await ro.checkToken(), false);
  assert.equal(await bad.checkToken(), false);
});

test("checkToken rejects classic or OAuth tokens without calling the API", async () => {
  const fetch = fakeFetch([]);

  assert.equal(await createStore({ repo: "o/r", token: "ghp_classic", fetch }).checkToken(), false);
  assert.equal(fetch.calls.length, 0);
});
