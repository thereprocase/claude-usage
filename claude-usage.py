#!/usr/bin/env python3
"""claude-usage: 90-day usage heatmap and summary from Claude Code transcripts."""

import os
import json
import glob
from datetime import date, timedelta
from collections import defaultdict

# ── ANSI ─────────────────────────────────────────────────────────────────────
R    = '\033[0m'
DIM  = '\033[2m'
BOLD = '\033[1m'

def fg(c):
    return f'\033[38;5;{c}m'

SPIKE_C  = fg(196)  # red — 5-hour spike
WEEKLY_C = fg(201)  # magenta — weekly breach
GRAY_C   = fg(240)  # no data

# 20-step gradient: blue → cyan → green → yellow → orange
# 4 shape bands × 5 color steps. Red/magenta reserved for alarms only.
GRADIENT = [
    # Band 1: ░ light shade — "barely there"
    (21,  '░'), (27,  '░'), (33,  '░'), (39,  '░'), (45,  '░'),
    # Band 2: ▒ medium shade — "moderate"
    (51,  '▒'), (50,  '▒'), (49,  '▒'), (48,  '▒'), (47,  '▒'),
    # Band 3: ▓ dark shade — "heavy"
    (46,  '▓'), (82,  '▓'), (118, '▓'), (154, '▓'), (190, '▓'),
    # Band 4: █ full block — "maxed out"
    (226, '█'), (220, '█'), (214, '█'), (208, '█'), (202, '█'),
]

# ── Config ────────────────────────────────────────────────────────────────────
claude_dir   = os.path.expanduser('~/.claude')
projects_dir = os.path.join(claude_dir, 'projects')
log_file     = os.path.join(claude_dir, 'rate-limit-log.jsonl')
today        = date.today()
cutoff       = today - timedelta(days=90)

# ── Collect data ──────────────────────────────────────────────────────────────
# day -> {tokens, turns, models: {}, projects: {}}
days          = defaultdict(lambda: {'tokens': 0, 'turns': 0,
                                     'models': defaultdict(int),
                                     'projects': defaultdict(int)})
model_totals   = defaultdict(int)
project_totals = defaultdict(int)
total_tokens   = 0
total_turns    = 0
total_sessions = set()

for jsonl_path in glob.glob(os.path.join(projects_dir, '**', '*.jsonl'), recursive=True):
    session_id = os.path.basename(jsonl_path).replace('.jsonl', '')
    try:
        with open(jsonl_path, encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except Exception:
                    continue
                if entry.get('type') != 'assistant':
                    continue
                msg   = entry.get('message', {})
                usage = msg.get('usage', {})
                if not usage:
                    continue
                ts = entry.get('timestamp', '')
                try:
                    d = date.fromisoformat(ts[:10])
                except Exception:
                    continue
                if d < cutoff or d > today:
                    continue

                # Weight: input + cache_creation + output (exclude cache_read = reuse)
                tokens = (usage.get('input_tokens', 0)
                        + usage.get('cache_creation_input_tokens', 0)
                        + usage.get('output_tokens', 0))
                if tokens == 0:
                    continue

                model = msg.get('model', 'unknown')
                if   'opus'    in model: mshort = 'opus'
                elif 'sonnet'  in model: mshort = 'sonnet'
                elif 'haiku'   in model: mshort = 'haiku'
                else:                    mshort = model[:12]

                cwd   = entry.get('cwd', '')
                parts = cwd.replace('\\', '/').rstrip('/').split('/') if cwd else []
                proj  = '/'.join(parts[-2:]) if len(parts) >= 2 else (parts[-1] if parts else 'unknown')

                days[d]['tokens']           += tokens
                days[d]['turns']            += 1
                days[d]['models'][mshort]   += tokens
                days[d]['projects'][proj]   += tokens
                model_totals[mshort]        += tokens
                project_totals[proj]        += tokens
                total_tokens                += tokens
                total_turns                 += 1
                total_sessions.add(session_id)
    except Exception:
        continue

# ── Rate limit crossings — separate 5-hour and weekly ────────────────────────
spike_days = set()   # days with 5-hour ≥95%
weekly_breach_weeks = set()  # ISO week numbers with 7-day ≥95%

try:
    with open(log_file, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                d = date.fromisoformat(e.get('ts', '')[:10])
                if d < cutoff or d > today:
                    continue
                window = e.get('window', '')
                threshold = e.get('threshold', 0)
                if threshold >= 95:
                    if window == 'five_hour':
                        spike_days.add(d)
                    elif window == 'seven_day':
                        # Store as (year, iso_week) tuple
                        yr, wk, _ = d.isocalendar()
                        weekly_breach_weeks.add((yr, wk))
            except Exception:
                continue
except FileNotFoundError:
    pass

# ── Intensity: 20-level rank-based scale ─────────────────────────────────────
# Assign level 0-19 by rank position among days with usage.
active_sorted = sorted((d for d in days if days[d]['tokens'] > 0),
                       key=lambda d: days[d]['tokens'])
n = len(active_sorted)
rank_level = {}
for i, d in enumerate(active_sorted):
    rank_level[d] = min(int(i / max(n, 1) * 20), 19)

def cell(d):
    """Return (colored_char, is_spike) for a day."""
    lvl = rank_level.get(d, -1)
    if d in spike_days:
        return f'{SPIKE_C}▲{R}', True
    if lvl < 0:
        return f'{GRAY_C}·{R}', False
    color, glyph = GRADIENT[lvl]
    return f'{fg(color)}{glyph}{R}', False

# ── Heatmap ───────────────────────────────────────────────────────────────────
# 13 weeks × 7 days, Monday-anchored, weeks as columns
start = today - timedelta(days=today.weekday()) - timedelta(weeks=12)

DAY_LABELS = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']

print()
print(f'{BOLD}Claude Usage — last 90 days{R}')
print()

# Week ID row — aligned with columns
wk_row = '      '
for w in range(13):
    d = start + timedelta(weeks=w)
    yr, wk, _ = d.isocalendar()
    wk_row += f'{DIM}W{wk:<2}{R}'
print(wk_row)

# Heatmap rows
for dow in range(7):
    row = f'{DIM}{DAY_LABELS[dow]}{R}    '
    for w in range(13):
        d = start + timedelta(weeks=w, days=dow)
        if d > today:
            row += '   '
            continue
        ch, _ = cell(d)
        row += f'{ch}  '
    print(row)

# Weekly breach marker row
breach_row = '      '
for w in range(13):
    d = start + timedelta(weeks=w)
    yr, wk, _ = d.isocalendar()
    if (yr, wk) in weekly_breach_weeks:
        breach_row += f'{WEEKLY_C}▼{R}  '
    else:
        breach_row += '   '
# Only print if there are any breaches (avoid empty row)
if weekly_breach_weeks:
    print(breach_row)

print()

# ── Legend ────────────────────────────────────────────────────────────────────
legend = f'{DIM}Legend:{R}  '
legend += f'{fg(21)}░{R}{DIM}low{R}  '
legend += f'{fg(51)}▒{R}{DIM}mod{R}  '
legend += f'{fg(82)}▓{R}{DIM}heavy{R}  '
legend += f'{fg(226)}█{R}{DIM}max{R}  '
legend += f'{SPIKE_C}▲{R}{DIM}5hr≥95%{R}  '
legend += f'{WEEKLY_C}▼{R}{DIM}wk≥95%{R}'
print(legend)
print()

# ── Summary ───────────────────────────────────────────────────────────────────
def fmt_tok(t):
    if t >= 1_000_000: return f'{t / 1_000_000:.1f}M'
    if t >= 1_000:     return f'{t / 1_000:.0f}k'
    return str(t)

def spark_bar(frac, width=16):
    filled = max(1, int(frac * width)) if frac > 0 else 0
    return '█' * filled + '░' * (width - filled)

peak_day    = max(days, key=lambda d: days[d]['tokens']) if days else None
peak_tokens = days[peak_day]['tokens'] if peak_day else 0

print(f'{BOLD}Last 90 days:{R}  {total_turns} turns | {fmt_tok(total_tokens)} tokens | {len(total_sessions)} sessions')
if peak_day:
    print(f'{BOLD}Peak day:{R}      {peak_day} — {fmt_tok(peak_tokens)} tokens')

# By project (top 8 + other)
if project_totals and total_tokens:
    print()
    print(f'{BOLD}By project:{R}')
    top = sorted(project_totals.items(), key=lambda x: x[1], reverse=True)[:8]
    other_tok = sum(v for k, v in project_totals.items() if k not in dict(top))
    col = max(len(k) for k, _ in top)
    for proj, tok in top:
        f = tok / total_tokens
        print(f'  {proj:<{col}}  {spark_bar(f)} {f*100:.0f}%')
    if other_tok:
        f = other_tok / total_tokens
        print(f'  {"other":<{col}}  {spark_bar(f)} {f*100:.0f}%')

# By model
if model_totals and total_tokens:
    print()
    print(f'{BOLD}By model:{R}')
    col = max(len(k) for k in model_totals)
    for mod, tok in sorted(model_totals.items(), key=lambda x: x[1], reverse=True):
        f = tok / total_tokens
        print(f'  {mod:<{col}}  {spark_bar(f)} {f*100:.0f}%')

# Rate limit summary
print()
spike_count = len(spike_days)
breach_count = len(weekly_breach_weeks)
if spike_count or breach_count:
    parts = []
    if spike_count:
        parts.append(f'{SPIKE_C}▲{R} {spike_count} day{"s" if spike_count != 1 else ""} with 5hr spike')
    if breach_count:
        parts.append(f'{WEEKLY_C}▼{R} {breach_count} week{"s" if breach_count != 1 else ""} at weekly limit')
    print(f'{BOLD}Rate limits:{R}   {"  ".join(parts)}')
else:
    # Distinguish "no crossings logged" from "no log file" (statusline not installed)
    if os.path.exists(log_file):
        print(f'{BOLD}Rate limits:{R}   no 95% crossings in this period')
    else:
        print(f'{BOLD}Rate limits:{R}   {DIM}no 95% crossing data available (install claude-statusline){R}')

print()
