# Release management

Canonical release process for tagbase-server. This file in git is the source of truth. The GitHub wiki [Release Management Guide](https://github.com/tagbase/tagbase-server/wiki/Release-Management-Guide) is stale; do not follow bump/publish dispatch instructions there.

Installation, Operations, System Architecture, and OpenAPI still live on the [project wiki](https://github.com/tagbase/tagbase-server/wiki). Only release management moved in-tree (the `docs/` directory is gitignored).

## What replaced the old workflow

Until this change, [`.github/workflows/release.yml`](https://github.com/tagbase/tagbase-server/blob/main/.github/workflows/release.yml) (now deleted) was a two-phase `workflow_dispatch`:

1. **bump** — open a `release/vX.Y.Z` PR that string-replaced every occurrence of the old version, including the public URL `/tagbase/api/v0.14.0`.
2. **publish** — after merge, tag `main` and `gh release create --generate-notes`.

Nothing ran on a schedule. The human picked the version. Merge of the bump PR did **not** create the GitHub Release.

That path is gone. There is no version-bump PR. [semantic-release](https://github.com/semantic-release/semantic-release) analyzes Conventional Commits on `main`, chooses the next version, rewrites an **explicit** file list, appends [`CHANGELOG.md`](../CHANGELOG.md), commits, tags `vMAJOR.MINOR.PATCH`, and publishes a GitHub Release.

## What a release contains

- Annotated Git tag `vMAJOR.MINOR.PATCH` on `main` (`tagFormat`: `v${version}` in [`.releaserc.json`](../.releaserc.json)).
- A GitHub Release whose body is generated from Conventional Commits since the previous tag (not GitHub’s `--generate-notes`).
- Root [`CHANGELOG.md`](../CHANGELOG.md): seeded from historical GitHub Releases, then owned by `@semantic-release/changelog`. Do not edit it by hand.
- Package/service version strings set to that tag (`v` prefix, same as today):
  - [`tagbase_server/pyproject.toml`](../tagbase_server/pyproject.toml)
  - [`tagbase_server/setup.py`](../tagbase_server/setup.py)
  - OpenAPI `info.version` in root [`openapi.yaml`](../openapi.yaml) and [`tagbase_server/tagbase_server/openapi/openapi.yaml`](../tagbase_server/tagbase_server/openapi/openapi.yaml)
  - [`tagbase_server/tagbase_server/telemetry.py`](../tagbase_server/tagbase_server/telemetry.py) `SERVICE_VERSION`

The **HTTP API prefix is not the package version.** It is major-only, from [`tagbase_server/tagbase_server/api_prefix.py`](../tagbase_server/tagbase_server/api_prefix.py):

| Package version       | Public prefix     |
| --------------------- | ----------------- |
| `0.x`                 | `/tagbase/api/v0` |
| `1.x` (first `1.0.0`) | `/tagbase/api/v1` |

Old `/tagbase/api/v0.14.0` is not redirected; it 404s. Tests, nginx `/docs` proxy, compose ingest base, and OpenAPI `servers.url` follow the major-only prefix. Do **not** globally `sed` the version string — that is how the URL used to track every patch.

`1.0.0` is the first **breaking** Conventional Commit on `0.x` (not a human-typed version). After that, the version script rewrites `/tagbase/api/v0` → `/tagbase/api/v1` in the prefix file list.

## When a release runs

Workflow: [`.github/workflows/semantic-release.yml`](../.github/workflows/semantic-release.yml) ([Actions](https://github.com/tagbase/tagbase-server/actions/workflows/semantic-release.yml)).

It does **not** run on push to `main` (avoids a tag per merge and a loop when the bot commits the changelog). The job only runs if `github.ref == refs/heads/main`.

| Trigger                              | Behavior                                                                                                                                                                                                                                                                                                                               |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Cron `0 15 * * 1` (Monday 15:00 UTC) | Run [scripts/semantic-release-fortnight-gate.sh](../scripts/semantic-release-fortnight-gate.sh). If the newest `v*` tag is **fewer than 14 days** old, print `skip=true` and stop (job still green). Otherwise run semantic-release. GitHub cron cannot express “every other Monday”; the weekly cron plus this gate is the fortnight. |
| `workflow_dispatch`                  | Same job, **no** 14-day gate. “Release now” if there are releasable commits.                                                                                                                                                                                                                                                           |

Empty windows: if semantic-release finds no commits that map to a bump, it exits 0 with **no** tag and **no** GitHub Release.

Concurrency group `tagbase-semantic-release` does not cancel in-progress runs.

## Version mapping (Conventional Commits)

Analyzer: Angular preset plus extra `releaseRules` in [`.releaserc.json`](../.releaserc.json).

| Commit                                                                     | Bump                    |
| -------------------------------------------------------------------------- | ----------------------- |
| `feat`                                                                     | minor                   |
| `BREAKING CHANGE` in footer, or `type!:`                                   | major (`0.x` → `1.0.0`) |
| `fix`, `perf`, `chore`, `docs`, `style`, `refactor`, `test`, `ci`, `build` | patch                   |

Renovate titles such as `chore(deps): …` are patches when a release actually runs. A deps-only fortnight still ships a patch if the 14-day gate passes.

## Pull request lint (commitlint)

[`.github/workflows/commitlint.yml`](../.github/workflows/commitlint.yml) runs on `opened` / `synchronize` / `reopened` / `edited`. It fails if:

- any commit from the PR base SHA to the head SHA is not Conventional, or
- the **PR title** is not Conventional (`@commitlint/config-conventional`).

Pinned in the workflow via `npx` (no root `package.json`): `@commitlint/cli@21.2.2` and `@commitlint/config-conventional@21.2.2`. Config: [`commitlint.config.cjs`](../commitlint.config.cjs). There is no Husky hook; CI is the gate.

Agents: see [AGENTS.md](../AGENTS.md) Commits. Do not commit unless the user asks.

## Tooling map

```text
.github/workflows/semantic-release.yml   # cron + dispatch; Node 24; npx semantic-release
.github/workflows/commitlint.yml         # PR title + commits
.releaserc.json                          # plugins, releaseRules, git assets, tagFormat
scripts/semantic-release-fortnight-gate.sh
scripts/set-release-version.py           # package version + major-only URL prefix
tagbase_server/tagbase_server/api_prefix.py
CHANGELOG.md
commitlint.config.cjs
```

### semantic-release plugins (in order)

1. `@semantic-release/commit-analyzer` — next bump type.
2. `@semantic-release/release-notes-generator` — notes for GitHub + changelog.
3. `@semantic-release/changelog` — rewrite `CHANGELOG.md`.
4. `@semantic-release/exec` — `python3 scripts/set-release-version.py ${nextRelease.version}`.
5. `@semantic-release/git` — commit the asset list with `chore(release): ${nextRelease.version} [skip ci]`.
6. `@semantic-release/github` — create the GitHub Release.

The default npm plugin is **not** used (this is a Python repo). Versions are pinned on the `npx --package` line in the workflow (`semantic-release@25.0.9`, changelog `7.0.0`, exec `7.1.0`, git `11.0.1`).

### `set-release-version.py`

- Argument: `MAJOR.MINOR.PATCH` or `vMAJOR.MINOR.PATCH`.
- Writes `v…` into the package-version files (exactly one match per pattern).
- Sets `API_PREFIX` and replaces `/tagbase/api/vN` or `/tagbase/api/vN.N.N` in the prefix file list (nginx, OpenAPI servers/examples, compose, build.yml stack probe, package README). Does **not** rewrite this wiki page or `CHANGELOG.md` history.

Local check (does not commit):

```bash
python3 scripts/set-release-version.py 0.14.0
```

### Auth and CI

`GITHUB_TOKEN` only (job `contents: write` and `issues: write`). No PAT or GitHub App. Checkout uses `persist-credentials: true`, `fetch-depth: 0`, `fetch-tags: true`, `ref: main`.

The release commit does not start other workflows (`GITHUB_TOKEN` push + `[skip ci]` in the message). Branch protection on `main` may still block the git plugin; if a release job fails on push, that is the first place to look.

## Maintainer commands

Release now (skips the 14-day gate; still no-ops if there is nothing to release):

```bash
gh workflow run semantic-release.yml --ref main
```

Inspect the last tags:

```bash
git fetch --tags origin
git tag --list 'v[0-9]*' --sort=-v:refname | head
```

Dry-run the fortnight gate locally (needs tags):

```bash
bash scripts/semantic-release-fortnight-gate.sh schedule
bash scripts/semantic-release-fortnight-gate.sh workflow_dispatch
```

Do not run `release.yml`. Do not open `release/v*` bump PRs.

## Failure modes

| Symptom                                 | Likely cause                                                                              |
| --------------------------------------- | ----------------------------------------------------------------------------------------- |
| Scheduled job green, no tag             | Gate skipped (`< 14` days) or no releasable commits.                                      |
| Dispatch green, no tag                  | No Conventional Commits since last tag that match `releaseRules`.                         |
| `set-release-version.py` exits non-zero | A listed file no longer matches the expected pattern (URL or version string).             |
| Git plugin cannot push                  | `main` protection or missing `contents: write`.                                           |
| commitlint red on this PR               | Title or a commit is not Conventional (squash-merge still needs a Conventional PR title). |

## Related CI (not the releaser)

[Super Linter](../.github/workflows/super-linter.yml) runs on pull requests and on push to `main` only (not on every feature-branch push), so same-repo PRs get one lint job.
