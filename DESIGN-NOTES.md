# Design Notes: Usage Graph Visualization

**Date:** 2026-04-03
**Designer:** Frodo (UX review agent)
**Implementer:** Coordinator (trio-dev)
**Channel:** `skill-cleanup` trio session

These notes capture the UX rationale behind the usage graph's visual design. If you're maintaining or extending the heatmap, read this before changing colors, glyphs, or layout.

---

## Core Principle: Separate the Data Channels

The heatmap carries three independent signals. Each gets its own visual channel so they don't compete for attention:

| Signal | Channel | Encodes |
|--------|---------|---------|
| Daily volume | Cell color + shape | How much did I use today? |
| 5-hour spike | Glyph override (▲) | Did the rolling window hit ≥95%? |
| Weekly breach | Marker row (▼) | Did the 7-day limit hit ≥95%? |

Mixing signals into one visual element (e.g., changing cell color for both volume AND spikes) creates ambiguity. Keeping them separate means each can be read independently or together.

---

## The Gradient: Blue → Cyan → Green → Yellow → Orange

### Why not include red?

Red is reserved exclusively for alarm markers (▲). If the volume gradient included red, a high-usage day and a rate-limit spike would look the same. Pulling red out of the gradient makes it unambiguous: if you see red, something hit a limit. Period.

The gradient stops at deep orange (ANSI 202). The warmest volume color is still "warm" enough to feel like heavy usage without triggering the "something is wrong" association that red carries.

### Why 20 steps?

Repro asked for high granularity. The ANSI 256-color cube supports smooth walks where each step changes exactly one RGB component by one level. The 20-step gradient walks:

```
Blue (0,0,5) → Cyan (0,5,5) → Green (0,5,0) → Yellow (4,5,0) → Orange (5,1,0)
```

Each step is perceptually distinct on most terminals. The cyan-to-green transition (steps 6-10) is the tightest perceptually — if any two steps are indistinguishable on a particular terminal, dropping to 16 levels (4×4) is a safe fallback.

### Why 4 shape bands?

The Unicode block elements ░▒▓█ provide density encoding independent of color:

| Shape | Band | Meaning |
|-------|------|---------|
| ░ | 1-5 | Barely there |
| ▒ | 6-10 | Moderate |
| ▓ | 11-15 | Heavy |
| █ | 16-20 | Maxed out |

This makes the heatmap readable in monochrome. A user who can't distinguish colors (or is on a limited terminal) still gets 4 density levels from shape alone. The shape bands also make the gradient non-linear perceptually — each band transition is a visible "click" that prevents the smoothness from washing out into mush.

---

## Shape Over Color: The Accessibility Principle

Every distinct state in the heatmap is distinguishable by shape alone, without any color:

| State | Shape | Color (secondary) |
|-------|-------|-------------------|
| Volume (4 bands) | ░ ▒ ▓ █ | Blue→orange gradient |
| 5-hour spike | ▲ | Red (196) |
| Weekly breach | ▼ | Magenta (201) |
| No data | · | Gray (240) |

The alarm markers (▲▼) are completely outside the ░▒▓█ shape family. You cannot confuse an alarm with a volume cell even in grayscale. The triangles are also a paired set — same family, different direction — which makes them feel related but distinct:

- ▲ points up = alert within the day (localized)
- ▼ points down = weight of the whole week bearing down (aggregated)

### Colorblind safety

Orange vs. red is the worst pair for deuteranopia (~8% of males). By using shape as the primary differentiator and color as secondary, the design sidesteps this entirely. The magenta (201) choice for weekly markers adds a third axis of distinction — magenta is maximally separated from both the warm gradient and the red alarm in all color vision types.

---

## The ▼ Marker Row

### Why a separate row instead of marking individual cells?

The weekly breach is a span event (7 days), not a point event. Marking individual cells within the week would:
1. Visually merge with the ▲ spike markers, creating confusion
2. Imply the breach happened "on" specific days rather than across the whole window
3. Clutter cells that already carry volume + potential spike data

A dedicated row below Sunday keeps the weekly signal spatially separated. You can scan just the bottom row to see "which weeks were dangerous" across the entire 90-day window — ~13 positions, instantly scannable.

### Why ▼ specifically?

- ▲ (up) for spikes and ▼ (down) for weekly creates a visual pairing
- ━━━ (continuous line) reads as a border, not a signal
- ◆ (diamond) has no semantic relationship to ▲
- ▼ placed below the grid feels like the weight of the week pressing down

On weeks with no breach, the row is blank (spaces). The ▼ only appears when something's wrong — absence is the happy path.

---

## Color Assignments (ANSI 256)

| Element | Glyph | ANSI Code | Hex Approx | Rationale |
|---------|-------|-----------|------------|-----------|
| Volume band 1 start | ░ | 21 | #0000FF | Deep blue — quiet start |
| Volume band 2 start | ▒ | 51 | #00FFFF | Bright cyan — moderate |
| Volume band 3 start | ▓ | 46 | #00FF00 | Pure green — getting active |
| Volume band 4 start | █ | 226 | #FFFF00 | Bright yellow — heavy |
| Volume band 4 end | █ | 202 | #FF5F00 | Deep orange — ceiling |
| 5-hour spike | ▲ | 196 | #FF0000 | Red — maximum alarm contrast |
| Weekly breach | ▼ | 201 | #FF00FF | Magenta — distinct from red AND gradient |
| No data | · | 240 | #585858 | Dim gray — invisible until needed |

### Why fixed color for ▲, not volume-colored?

If ▲ inherited the cell's volume color, a cyan ▲ on a light-usage day would disappear into the grid. The spike marker needs to pop regardless of surrounding context. A fixed red ▲ is always visible because red never appears elsewhere in the visualization.

---

## What We Deliberately Did NOT Do

1. **No dual encoding on spike cells.** A cell that has both a 5-hour spike (▲) AND is part of a weekly-breach week gets no special treatment beyond the ▲ itself. The ▼ in the marker row already flags the week. Doubling up adds noise without information.

2. **No intermediate threshold markers.** The old system logged at [30%, 55%, 75%, 99%]. Repro found this too noisy — it answered "how close am I?" when the real question is "did I hit the wall?" The new system logs only at ≥95%, which is the only threshold that matters for workflow disruption.

3. **No color interpolation within cells.** Each of the 20 steps maps to exactly one ANSI color code. No blending, no background colors, no dimming. Terminal rendering is unpredictable enough without trying to layer foreground and background colors.

---

## Future Considerations

- **Oscillation testing.** If the rate limit value bounces around 95% within a single status line cycle (drops to 94%, comes back to 96%), the deduplication logic should prevent double-logging. This is worth a dedicated test case.

- **Terminal compatibility.** The 20-step gradient relies on ANSI 256-color. On terminals with only 16 colors, the gradient would collapse. If this becomes an issue, a 4-step fallback (one per shape band, using basic ANSI colors) would preserve readability.

- **Dark vs. light terminals.** The current palette assumes a dark background. On a light terminal, the gray no-data dots (240) would be invisible. If light-terminal support matters, the no-data glyph would need a brighter fallback.
