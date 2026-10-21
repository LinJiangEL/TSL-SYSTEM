CHANGELOG Document  [English](/CHANGELOG.md) | [Chinese](/CHANGELOG_CN.md)

# Changelog
All notable changes to TSL-SYSTEM are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 7.5.0 - 2026-10-21

### Added
- **Music module** (`tools/Music`): a local music library, the point-song station opened by `execute Music`
  (`search`, `local`, `list`, `info`, `get`, `queue`, `drop`, `clear`, `dir`, `play`, `pause`, `stop`) and
  background playback through MCI on Windows or `ffplay` on Linux, so the terminal is never blocked.
- **Online music crawler** (`tools/Music/crawler.py`): Netease Cloud Music and Kugou sources, merged and
  de-duplicated search results, streaming download with `.part` files and `os.replace`, content-type and
  size validation, and clear `CrawlerError` messages for copyright-restricted tracks.
- **Terminal music commands**: `music play|stop|pause`, `music search KEYWORD` and
  `music get INDEX/KEYWORD`; playback state and control files allow every TSL-SYSTEM process to control
  the playback owned by another one.
- **Network module** (`tools/Network`): a standard-library DNS client (A/AAAA/CNAME/MX/NS/TXT/SRV/CAA),
  `ping`, `trace` (traceroute), threaded TCP `ports` scanning, `http` analysis (status, headers, redirects,
  timings, security headers, cookies), `tls` certificate inspection, RFC 3912 `whois`, `local` interface /
  gateway / ARP inspection, `public` IP and location, `speed` download test and an aggregate `analyze HOST`.
- **Function analysis mode** (`tools/Mathematics/cal_function.py`): a standalone plotting REPL opened in a
  new console (`@window` from advanced mode). It accepts curves (`y1=x+2`), functions (`f(x)=2x+1`),
  evaluation (`f(2)`), variables, `range`/`ylim` viewport control, duplicate exclusion, PNG export and an
  ASCII fallback renderer.
- **Breakpoint protection** (`guard.py`): a checkpoint in `Temp/Breakpoint.state` rewritten before every
  command, crash / interrupt / signal / thread records in `Temp/logs/log_breakpoint.log`,
  `faulthandler` dumps in `Temp/logs/log_fault.log`, a recovery warning on the next launch, and a `throw`
  command to test the mechanism on purpose.
- **Unified terminal UI helpers** (`tools/__built_in__/style.py`): banners, rules, headings, labels and
  coloured success / warning / error output, applied to `terminal.py`, `system.py`, `loading.py`, the
  `help` table and every tool module.
- **Operation logging** for terminal commands, user management, backup / restore, upgrade and the music,
  network and mathematics modules, tagged with `[CMDINFO]`, `[USERINFO]`, `[PROCESSINFO]` and
  `[MUSICINFO]`.

### Changed
- **Mathematics**: unified result blocks (`Expression`, `Result (2)`, `Digits`, `Fraction`, `Sqrt`) with
  exact `Fraction` arithmetic and scientific notation for huge exact values; rewritten REPLs with
  regex-based argument parsing, command aliases and unified `ErrorName: message.` errors. Commands which
  take no argument must be prefixed with `@` (`@help`, `@exit`, `@flush`, `@window`, ...), and `@exit`
  returns directly to the terminal.
- **`trunc`** restored as a SuperUser shell escape: the raw command line is forwarded to the mother
  system (`cmd /C` on Windows, `/bin/sh -c` on Linux) and the exit code is reported and logged.
- **Music storage** moved from the repository-level `Music/` directory to `tools/Music/Musics`
  (still overridable with the `TSL_MUSIC_DIR` environment variable).
- **`execute`** now lists `Network` as available; `Chemistry`, `MultiMedia` and `Philosophy` remain in
  development.
- The `user@TSL-SYSTEM` prompt keeps its original uncoloured form, while banners, hints and messages are
  styled.
- **Version** bumped from `5.17.4` to `7.5.0`.

### Fixed
- `trunc` no longer breaks quoted arguments: `trunc python -c "import os"`, paths containing spaces and
  shell pipes now work, because the command line is passed to the shell as one string instead of a
  re-escaped argument list.
- `music pause` and `music stop` now affect playback owned by another TSL-SYSTEM process, and MCI thread
  affinity (error 263) is handled by a dedicated playback engine thread.
- `LoggerManager` no longer fails to index the log directory when extra log files (for example
  `log_breakpoint.log` and `log_fault.log`) exist.
- Compound mathematics: unary signs, parentheses, `^`, `//`, `%` and operator precedence are evaluated
  correctly with exact fractions, and invalid input raises structured errors instead of crashing.
- Terminal commands (`internal`, `backup`, `upgrade`) now report and log non-zero exit codes instead of
  claiming success.
- The Windows `trunc` exit status is propagated to the terminal prompt instead of being silently dropped.

### Removed
- The `exit` command at the Mathematics mode-selection menu (use `@exit` instead).
- Music is no longer stored in a repository-level `Music/` directory; the files live in
  `tools/Music/Musics`.

### Security
- `trunc` remains SuperUser-only and never uses `shell=True`.

## Earlier versions
Versions before `7.5.0` were not tracked in this changelog; their history is recorded in the Git history
(`git log`) since the initial commit on 2024-05-01.
