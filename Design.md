# Design.md — Visual Design Guidelines

## Overall Theme
Developer-tool aesthetic: clean, technical, trustworthy — think security dashboard, not consumer app. Dark mode as default (matches the target audience: developers), with a light mode toggle optional.

## Color Palette

### Dark mode (default)
| Role | Color | Hex |
|---|---|---|
| Background (primary) | Near-black slate | `#0D1117` |
| Background (surface/cards) | Dark slate | `#161B22` |
| Border/divider | Muted gray | `#30363D` |
| Text (primary) | Off-white | `#E6EDF3` |
| Text (secondary/muted) | Gray | `#8B949E` |
| Accent (brand/primary action) | Electric blue | `#58A6FF` |
| Severity — Critical | Red | `#F85149` |
| Severity — High | Orange | `#DB6D28` |
| Severity — Medium | Yellow | `#D29922` |
| Severity — Low | Green | `#3FB950` |

### Light mode (optional)
| Role | Color | Hex |
|---|---|---|
| Background (primary) | White | `#FFFFFF` |
| Background (surface/cards) | Light gray | `#F6F8FA` |
| Border/divider | Gray | `#D0D7DE` |
| Text (primary) | Near-black | `#1F2328` |
| Text (secondary/muted) | Gray | `#656D76` |
| Accent | Blue | `#0969DA` |
| Severity colors | Same hues as dark mode, slightly deepened for contrast on white |

## Typography
- **Headings**: `Inter` or `IBM Plex Sans` — clean, technical, highly legible.
- **Body text**: same family as headings for consistency, weight 400.
- **Code/monospace** (for file paths, code snippets, findings detail): `JetBrains Mono` or `Fira Code`.
- **Scale**: base 16px body, 14px for secondary/meta text, headings at 24/20/18px (h1/h2/h3).

## Layout Principles
- Dashboard-first: the findings table is the centerpiece of the results view, not buried under marketing-style hero sections.
- Severity is always visually encoded with both color AND a text label/icon — never color alone (accessibility).
- Generous whitespace around code snippets and citations so they're easy to scan, not cramped.
- Sidebar or top nav is minimal — this is a single-purpose tool, not a multi-page app.

## Component Notes
- **Findings table**: sortable by severity, filterable by category; each row expandable to show full explanation + citation + fix suggestion.
- **Progress indicator** (during audit run): show which pipeline stage is active (Parsing → Classifying → Retrieving → Generating Report) rather than a generic spinner — reinforces the multi-step agentic nature of the tool.
- **Citations**: rendered as small, clearly marked reference chips/links distinct from the AI-generated explanation text, so users can tell what's grounded vs. synthesized.
- **Dependency graph visualization** (if built): keep it minimal — nodes colored by risk level, not a cluttered force-directed mess.

## Tone
Professional, precise, non-alarmist. Findings should read like a security report, not a doomsday warning — clear severity, clear reasoning, clear next step.
