# claude-usage

90-day usage heatmap and summary for [Claude Code](https://claude.ai/code), pulled directly from your local transcript files. No API calls, no auth, no telemetry — just your data.

```
Claude Usage — last 90 days

      W2 W3 W4 W5 W6 W7 W8 W9 W10W11W12W13W14
Mo    ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ▒  ▒
Tu    ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ░  ▓
We    ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ░  ▓
Th    ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ▒  █
Fr    ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ▒  ▓  ▓
Sa    ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ░  █
Su    ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ░  █
                                          ▼

Legend:  ░low  ▒mod  ▓heavy  █max  ▲5hr≥95%  ▼wk≥95%

Last 90 days:  121981 turns | 418.6M tokens | 1038 sessions
Peak day:      2026-04-02 — 90.5M tokens

Rate limits:   ▼ 1 week at weekly limit
```

> Color-coded: blue→cyan→green→yellow→orange gradient (20 steps, 4 shape bands). Red `▲` for 5-hour rate limit spikes, magenta `▼` for weekly limit breaches. Red and magenta are reserved exclusively for alarms — they never appear in the volume gradient.

---

## What it does

Scans `~/.claude/projects/**/*.jsonl` — Claude Code's local transcript store — and aggregates:

- **Token usage** by day (input + cache_creation + output; cache_read excluded as reuse)
- **Session count** (unique `.jsonl` files touched in the window)
- **Turn count** (assistant messages with usage data)
- **Project breakdown** from the `cwd` field in each transcript entry
- **Model breakdown** (opus / sonnet / haiku)
- **Rate limit crossings** from `~/.claude/rate-limit-log.jsonl`

Intensity levels on the heatmap are rank-based quartiles across active days, so a single outlier spike doesn't wash out the rest of the grid.

---

## Platform support

| Platform | Works? | Notes |
|----------|--------|-------|
| macOS | ✅ | Native ANSI, bash launcher |
| Linux | ✅ | Native ANSI, bash launcher |
| Windows (Windows Terminal) | ✅ | Use PowerShell launcher |
| Windows (VS Code terminal) | ✅ | Use PowerShell launcher |
| Windows (plain cmd.exe) | ❌ | No ANSI 256-color support |

Python 3.8+, stdlib only — no external dependencies.

### Optional: Rate limit markers

The `▲` (5-hour spike) and `▼` (weekly breach) markers require [claude-statusline](https://github.com/thereprocase/claude-statusline) to be installed. The status line detects when rate limit windows hit ≥95% and logs events to `~/.claude/rate-limit-log.jsonl`. The usage graph reads that file.

**Without claude-statusline:** The heatmap renders normally with the full gradient, but no rate limit markers appear. The summary shows "no 95% crossing data available" instead of spike/breach counts.

**With claude-statusline:** Rate limit events are logged automatically on every Claude response. No additional configuration needed — install both tools and the markers appear.

---

## Install

### macOS / Linux / Windows (Git Bash or WSL)

```bash
curl -fsSL https://raw.githubusercontent.com/thereprocase/claude-usage/main/install.sh | bash
```

Or manually:

```bash
cp claude-usage.py ~/.claude/
cp claude-usage.sh ~/.claude/
chmod +x ~/.claude/claude-usage.sh
```

### Windows (PowerShell / Windows Terminal)

```powershell
irm https://raw.githubusercontent.com/thereprocase/claude-usage/main/install.ps1 | iex
```

Or manually:

```powershell
Copy-Item claude-usage.py  $HOME\.claude\
Copy-Item claude-usage.ps1 $HOME\.claude\
```

---

## Run

```bash
# macOS / Linux / Git Bash
bash ~/.claude/claude-usage.sh

# Windows (PowerShell)
pwsh $HOME\.claude\claude-usage.ps1

# Any platform — python directly
python ~/.claude/claude-usage.py
```

---

## Wire up as a Claude Code slash command (`/usage-graph`)

Add to `~/.claude/settings.json`:

```json
{
  "slash_commands": {
    "usage-graph": {
      "description": "Show 90-day Claude usage heatmap",
      "command": "bash ~/.claude/claude-usage.sh"
    }
  }
}
```

On Windows, swap `bash ~/.claude/claude-usage.sh` for `pwsh $HOME\.claude\claude-usage.ps1`.

Then type `/usage-graph` in any Claude Code session.

---

## How tokens are counted

Each assistant message in the transcript carries a `usage` block:

```json
{
  "input_tokens": 12847,
  "cache_creation_input_tokens": 4200,
  "cache_read_input_tokens": 31000,
  "output_tokens": 843
}
```

`claude-usage` sums `input + cache_creation + output`. Cache reads are excluded — they represent context already paid for in a prior turn, and counting them again would inflate totals significantly on long sessions.

---

## Files

| File | Purpose |
|------|---------|
| `claude-usage.py` | Main script — all logic |
| `claude-usage.sh` | Bash launcher (macOS / Linux / Git Bash) |
| `claude-usage.ps1` | PowerShell launcher (Windows) |
| `install.sh` | Bash one-liner installer |
| `install.ps1` | PowerShell one-liner installer |

---

## License

MIT
