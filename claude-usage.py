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
RED  = '\033[38;5;196m'
GRAY = '\033[38;5;238m'

# 5 intensity levels: empty → dark green → mid → bright green → peak
HEAT = [GRAY, '\033[38;5;22m', '\033[38;5;28m', '\033[38;5;34m', '\033[38;5;82m']
BLOCKS = ' ░▒▓█'

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

# ── Rate limit crossing days ──────────────────────────────────────────────────
rl_days = set()
try:
    with open(log_file, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                d = date.fromisoformat(e.get('ts', '')[:10])
                if cutoff <= d <= today:
                    rl_days.add(d)
            except Exception:
                continue
except FileNotFoundError:
    pass

# ── Intensity: rank-based quartiles of active days ───────────────────────────
# Assign level 1-4 by rank position among days with usage, so the heatmap
# shows relative patterns rather than compressing against outlier spikes.
active_sorted = sorted((d for d in days if days[d]['tokens'] > 0),
                       key=lambda d: days[d]['tokens'])
n = len(active_sorted)
rank_level = {}
for i, d in enumerate(active_sorted):
    if   i < n * 0.25: rank_level[d] = 1
    elif i < n * 0.50: rank_level[d] = 2
    elif i < n * 0.75: rank_level[d] = 3
    else:              rank_level[d] = 4

def intensity(d):
    return rank_level.get(d, 0)

# ── Heatmap ───────────────────────────────────────────────────────────────────
# 13 weeks × 7 days, Monday-anchored, weeks as columns
start = today - timedelta(days=today.weekday()) - timedelta(weeks=12)

DAY_LABELS = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']

print()
print(f'{BOLD}Claude Usage — last 90 days{R}')
print()

# Month label row — label appears on the first week that falls in each month
month_row = '      '
prev_mo   = None
for w in range(13):
    d  = start + timedelta(weeks=w)
    mo = d.strftime('%b')
    if mo != prev_mo:
        month_row += f'{DIM}{mo}{R} '
        prev_mo = mo
    else:
        month_row += '    '
print(month_row)

for dow in range(7):
    row = f'{DIM}{DAY_LABELS[dow]}{R}    '
    for w in range(13):
        d = start + timedelta(weeks=w, days=dow)
        if d > today:
            row += '  '
            continue
        lvl = intensity(d)
        if d in rl_days:
            row += f'{RED}▲{R} '
        else:
            row += f'{HEAT[lvl]}{BLOCKS[lvl]}{R} '
    print(row)

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

# By project (top 5 + other)
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

# Rate limits
print()
if rl_days:
    print(f'{BOLD}Rate limits:{R}   {RED}▲{R} {len(rl_days)} day{"s" if len(rl_days) != 1 else ""} with threshold crossings in this period')
else:
    print(f'{BOLD}Rate limits:{R}   no crossings in this period')

print()
