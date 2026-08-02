# Code signing policy

How releases of PoE Price Check are produced, who may approve them, and what
is signed.

## Status

**Builds are currently unsigned.** An application to
[SignPath Foundation](https://signpath.org) for free open-source code signing
is planned; this document exists because a published signing policy is one of
their conditions. Until a certificate is in place, Windows will warn that the
publisher is unknown.

> Once signing is active, this section is replaced by the attribution
> SignPath requires: *"Free code signing provided by [SignPath.io](https://signpath.io),
> certificate by [SignPath Foundation](https://signpath.org)."*

## Team and roles

This is a single-maintainer project, so one person currently holds every role.
That is stated plainly rather than dressed up as a team.

| Role | Who | What they may do |
| --- | --- | --- |
| Author | [@Fearrrrrrrrrrwq](https://github.com/Fearrrrrrrrrrwq) | write and modify code |
| Reviewer | [@Fearrrrrrrrrrwq](https://github.com/Fearrrrrrrrrrwq) | approve pull requests |
| Approver | [@Fearrrrrrrrrrwq](https://github.com/Fearrrrrrrrrrwq) | decide that a build may be signed and released |

If further maintainers join, this table is updated in the same commit that
grants them access.

## Account security

- Multi-factor authentication is required on the GitHub account that owns this
  repository and on any SignPath account used for this project.
- Release artifacts may only be produced by the GitHub Actions workflow in
  [`.github/workflows/build.yml`](.github/workflows/build.yml). Nothing built on
  a personal machine is published.

## What gets built and signed

Only artifacts built by that workflow, from a tagged commit in this
repository, are eligible for signing:

- `poe-price-check.exe` — the application itself
- `poe-price-check-<version>.zip` — that executable plus a short readme

The build is reproducible from source with the same commands the workflow runs:

```
pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm poe-price-check.spec
python package.py
```

Every release publishes the SHA-256 of the executable in its release notes and
inside the archive, so anyone can check that the file they downloaded is the
file that was built.

## Release process

1. A change is committed to `main`. CI runs translation coverage checks and
   compiles every module.
2. The Approver creates a version tag (`v1.2.3`) and pushes it.
3. The workflow builds the executable on a clean GitHub-hosted Windows runner,
   packages it, verifies the archive contents, and creates the GitHub release.
4. No manual upload of binaries is possible in this process.

## What the software does

PoE Price Check reads item text that the user copies in Path of Exile, queries
the public pathofexile.com trade endpoints, and shows the result. It registers
a global keyboard hook — that is the only way to catch a shortcut while a game
has focus, and it is used for nothing else. It sends synthetic keystrokes to a
cloud gaming window only when the user presses the price-check shortcut.

It is not a hacking tool, contains no telemetry beyond an anonymous usage
counter, changes no system configuration, and bundles no third-party software.

## Privacy

The application sends an anonymous usage counter: version, operating system,
interface language, league, and how many price checks were run. It never sends
items, prices, account details, or the identifier of the user's bridge
document. The install identifier is random and linked to nothing. Telemetry is
switched off with `"telemetry": false` in `config.json`.

The project website counts page visits without cookies and without storing IP
addresses; the visitor identifier is a salted hash that changes every day.

Full details: [README](README.md#privacy).

## Reporting a problem

Open an issue at
[github.com/Fearrrrrrrrrrwq/poe-price-check/issues](https://github.com/Fearrrrrrrrrrwq/poe-price-check/issues).
For anything security-sensitive, use GitHub's private vulnerability reporting
on the same repository rather than a public issue.
