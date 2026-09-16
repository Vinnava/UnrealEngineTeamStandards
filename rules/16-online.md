# 21. The online module

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md).

**This section applies if the project talks to a backend service.** 1.1 defines the `<Project>Online`
module; this is what goes in it. Replication between game clients and a game server is section 11 -
a different problem with different rules.

---

### 21.1 The boundary

> **Wire types never leave the online module.**

- **A wire type is a `USTRUCT` that mirrors the payload** - named `F<Domain>Response`,
  `F<Domain>Request` - and it stays in the online module.
- **The service maps wire to domain at the boundary** and hands gameplay a domain type. Gameplay
  never sees a field named after someone else's database column.
- **Gameplay calls a service subsystem** (9.12), never `FHttpModule` directly.
- **The test:** the backend renames a field, and exactly one file changes.

### 21.2 Every request

Every outbound request declares four things, at the call site or in the service's config:

| Thing | Rule |
|---|---|
| **Timeout** | Always set. The engine default is generous and a hung request is indistinguishable from a broken feature |
| **Retry** | Exponential backoff with jitter, and a hard attempt cap. Never retry forever, never retry in a tight loop |
| **Cancellation** | Tied to the owner's lifetime - cancelled in `Deinitialize` or `EndPlay` (10.5) |
| **Failure behaviour** | What the player sees when it fails. "Nothing" is a decision, written down, not a default |

- **Only idempotent requests are retried automatically.** Retrying a purchase or a state mutation is
  how a player gets charged twice; those need a server-side idempotency key.
- **Never block the game thread on a request** (10.1). No synchronous HTTP, ever.
- **The response callback is a `UObject` lambda hazard** (10.2) - capture `TWeakObjectPtr`, resolve
  once, null-check, and check `GetWorld()` before anything world-dependent.
- **Queue or coalesce chatty calls.** One request per frame per system is already too many.

### 21.3 Never trust a response

- **Parse defensively.** Every field is checked; `TryGetField` leaves the output untouched on a miss
  (section 16), so a wire enum reserves 0 for `Unknown` (4.5).
- **A malformed response is a logged `Error` and a clean failure path** (6.6) - never an `ensure`
  (3.9), because the network is not a programmer error.
- **Validate ranges and lengths before use.** A negative currency value or a 10 MB display name is
  the server's bug and your crash.
- **Version the contract.** The client sends its version; the service can refuse it. A client that
  cannot tell an old server from a broken one cannot be diagnosed in the field.

### 21.4 Secrets and credentials

- **No secret in source control.** No API keys, signing secrets or service passwords in `.cpp`,
  `.ini`, or a `.uasset` - committed config is public to everyone with repository access, and
  extractable from a shipped build.
- **A shipped client holds no secret that matters.** Anything a client can reach, a player can
  extract. If a key must not leak, the call belongs on a server you control.
- **Tokens live in the platform's secure storage**, not in `SaveGame` and not in an ini.
- **Token refresh has exactly one owner** (9.4) and is idempotent - concurrent 401s must not start
  three refreshes.
- **Never log a token, a password, a session id or personal data** (6.6). Log a correlation id.
- **Clear credentials on sign-out**, including anything cached in memory.

### 21.5 Transport

- **HTTPS only.** No plaintext endpoint ships, including to a test environment.
- **Never disable certificate verification.** If a local development setup needs a bypass, gate it
  behind `#if !UE_BUILD_SHIPPING` (1.4), require an explicit ini opt-in, and log a loud `Warning`
  every time it engages - so it can never be quietly on in a build that ships.
- **Pin certificates where the platform supports it and the risk warrants it**, and write down the
  rotation plan in the same commit - an unrotatable pin is an outage waiting for an expiry date.
- **Endpoints are configuration, not constants** - per-environment config (9.6), so a build can be
  pointed at staging without a code change.

### 21.6 Offline, failure and the player

- **Every request has a defined offline behaviour**: queue it, fail it visibly, or degrade. Decide
  per request, write it in the service class.
- **A failure the player caused reads differently from one they did not.** "You are offline" is not
  "Something went wrong".
- **Never trap the player.** A failed call during a transition still lets them leave the screen.
- **A queued mutation survives a restart or it is not queued** - hold it with the save data (9.14),
  versioned like everything else.

### 21.7 Instrumentation

- **Every request carries a correlation id** and logs one line on send and one on completion, with
  status and duration (6.1). That pair is the whole of field diagnosis.
- **Count in-flight requests, failures and retries** (13.6) - these are the counters that show a
  backoff storm before support tickets do.
- **Log bodies only behind a development-only verbose flag**, never in Shipping, and never for an
  endpoint that carries personal data.

### 21.8 Testing

- **A fake backend is part of the module** - a local implementation behind the same interface (9.7),
  so gameplay is testable with no network and no account.
- **Inject failures deliberately**: timeout, 500, malformed body, expired token, offline mid-request.
  Each has a test (14.4); each has a defined player-facing result (21.6).
- **Wire parsing is pure logic and gets an automation test** (14.4) - it is exactly the kind of code
  that rule was written for.
