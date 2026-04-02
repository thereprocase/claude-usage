# claude-usage — Claude Context

## What this repo is

A two-file terminal tool: `claude-usage.py` does all the work, `claude-usage.sh` / `claude-usage.ps1` are thin launchers that set `PYTHONIOENCODING=utf-8` before calling it. That's the whole project.

## How it works

Reads `~/.claude/projects/**/*.jsonl` — Claude Code's local session transcripts. Each line is a JSON object. The script filters for `type == "assistant"` entries with a `usage` block, extracts token counts and metadata, and builds aggregates.

Key fields used from each entry:
- `timestamp` — ISO 8601, used to bucket by date
- `message.usage` — `input_tokens`, `cache_creation_input_tokens`, `output_tokens` (cache_read excluded)
- `message.model` — bucketed into opus/sonnet/haiku
- `cwd` — last two path segments used as project label
- `~/.claude/rate-limit-log.jsonl` — separate file, one entry per rate limit event, `ts` field used

## What NOT to change

- Token counting formula: `input + cache_creation + output`, cache_read excluded. This is intentional — changing it would break comparisons across time.
- Heatmap intensity: rank-based quartiles, not absolute thresholds. This prevents a single spike day from flattening everything else to level 1.
- The `.sh` and `.ps1` launchers are intentionally minimal. Don't add logic to them — keep it in the Python.

## Platform notes

The Python is stdlib-only and runs on 3.8+. The only platform-specific concern is ANSI 256-color output:
- macOS / Linux: works natively
- Windows Terminal / VS Code: works natively  
- Windows cmd.exe: does NOT support ANSI 256-color — will print garbage escape sequences

There is no `colorama` fallback. The intended fix for Windows is "use a real terminal," not adding a dependency.

## If the output looks wrong

Common causes:
- `PYTHONIOENCODING` not set → garbled Unicode block characters on Windows. The launchers handle this.
- No `.jsonl` files found → all-empty heatmap. Verify `~/.claude/projects/` exists and has session files.
- `rate-limit-log.jsonl` missing → script handles this gracefully (FileNotFoundError caught, no red markers shown).

## Slash command integration

The `/usage-graph` skill in Claude Code calls `bash ~/.claude/claude-usage.sh`. This is defined in `~/.claude/settings.json` as a slash command. The skill itself is in `~/.claude/skills/usage-graph/`.

## Repo layout

```
claude-usage.py    main script
claude-usage.sh    bash launcher
claude-usage.ps1   PowerShell launcher (Windows)
install.sh         bash one-liner install
install.ps1        PowerShell one-liner install
README.md          human docs
CLAUDE.md          this file
index.html         GitHub Pages landing page
```
