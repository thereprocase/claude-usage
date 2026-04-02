# claude-usage

90-day usage heatmap and summary for [Claude Code](https://claude.ai/code), pulled directly from your local transcript files. No API calls, no auth, no telemetry — just your data.

```
Claude Usage — last 90 days

      Jan             Feb             Mar
Mo      · · · · · · · · · · ▒ ▒
Tu      · · · · · · · · · · ░ ▲
We      · · · · · · · · · · ░ ▲
Th      · · · · · · · · · · ▓ ▲
Fr      · · · · · · · · · · ▒ ▓
Sa      · · · · · · · · · · ░ █
Su      · · · · · · · · · · ░ █

Last 90 days:  107776 turns | 385.4M tokens | 913 sessions
Peak day:      2026-04-02 — 77.5M tokens

By project:
  ClauDe/orcaPatch            █████░░░░░░░░░░░ 34%
  ClauDe/gridfinity           ███░░░░░░░░░░░░░ 21%
  ClauDe/fieldLog             █░░░░░░░░░░░░░░░  4%
  other                       ███░░░░░░░░░░░░░ 23%

By model:
  opus    ███████████░░░░░ 73%
  sonnet  ███░░░░░░░░░░░░░ 22%
  haiku   █░░░░░░░░░░░░░░░  6%

Rate limits:   ▲ 3 days with threshold crossings in this period
```

> The actual output is color-coded: green intensity heatmap, red `▲` for rate-limit days.

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
