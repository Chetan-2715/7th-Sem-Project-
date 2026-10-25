# Design.md — Visual Design & Frontend Component Guidelines

## Overall Aesthetic & Philosophy
The **Codebase Architecture & Risk Auditor** features an engineer-first, professional cybersecurity dashboard aesthetic. It prioritizes information density, legibility, and high-contrast visual cues over decorative marketing flair. Dark mode is the primary theme (slate `#0D1117`), inspired by developer IDEs and security command centers.

---

## Color Tokens & Design Palette

### Dark Theme Palette
| Token / Role | Color Name | Hex Code | Purpose |
|---|---|---|---|
| `bg-primary` | Slate Black | `#0D1117` | Main canvas background |
| `bg-surface` | Deep Slate | `#161B22` | Cards, modals, containers, table rows |
| `border-subtle` | Border Gray | `#30363D` | Card borders, table dividers, tab separators |
| `text-primary` | Crisp White | `#E6EDF3` | Headings, primary text, code identifiers |
| `text-secondary`| Muted Gray | `#8B949E` | Secondary captions, timestamps, file paths |
| `accent-primary`| Electric Blue | `#58A6FF` | Active tabs, buttons, primary focus outlines |
| `severity-critical` | Crimson Red | `#F85149` | Critical severity badge, critical nodes |
| `severity-high` | Security Orange | `#DB6D28` | High severity badge, high risk nodes |
| `severity-medium` | Amber Yellow | `#D29922` | Medium severity badge, medium risk nodes |
| `severity-low` | Forest Green | `#3FB950` | Low severity badge, clean health indicators |

---

## Typography Standards
- **UI Headings**: `Inter`, `SF Pro Display`, or system sans-serif — weights 600/700.
- **Body & Captions**: `Inter`, clean 400/500 weights for maximum readability.
- **Code & Identifiers**: `JetBrains Mono`, `Fira Code`, or `ui-monospace`.
- **Type Scale**:
  - `h1`: 24px / 32px line-height (Dashboard Header)
  - `h2`: 20px / 28px line-height (Section Titles)
  - `h3`: 16px / 24px line-height (Card Titles)
  - `body`: 14px / 20px line-height (General Text & Findings)
  - `code`: 13px / 18px line-height (Diff Viewer & Code Blocks)

---

## Core Visual Components

### 1. Multi-Modal Ingestion Selector (`AuditInput.jsx`)
- **4 Tab Layout**:
  1. **GitHub Repository**: Input field for public GitHub URLs with instant shallow clone.
  2. **ZIP Archive**: Drag-and-drop file upload zone with path traversal security.
  3. **Single File**: Instant source file uploader for fast inspections.
  4. **Raw Code Snippet**: Interactive multi-line code editor with real-time language detection.
- **Auto-Detected Language Badge**:
  - Dynamically detects the submitted language (Python, JavaScript, TypeScript, Java, C, C++, PHP, SQL, Go, Rust).
  - Renders a pill badge (e.g. `⚡ Detected: Python` or `⚡ Detected: Java`) so the user has immediate visual confirmation of the parsing engine.

### 2. Multi-Stage Pipeline Progress Bar (`ProgressBar.jsx`)
- Rather than displaying a generic spinner, the progress bar exposes the real-time agent workflow state:
  1. `[1/5] Ingesting Codebase & Resolving Dependencies`
  2. `[2/5] Running Neural CodeBERT & Polyglot Syntax Scanner`
  3. `[3/5] Querying FAISS Vector RAG Knowledge Base`
  4. `[4/5] Parallel AI Patch Synthesis (Gemini 2.5 Flash)`
  5. `[5/5] Compiling Security Audit Report`

### 3. Security Health Score Dial (`HealthScoreGauge.jsx`)
- Circular SVG gauge displaying the overall repository health score (0–100).
- Dynamically colored based on score thresholds:
  - `80 – 100`: Healthy (Green `#3FB950`)
  - `50 – 79`: Moderate Risk (Yellow `#D29922`)
  - `0 – 49`: High Danger (Red `#F85149`)

### 4. Metrics Summary Cards (`MetricCards.jsx`)
- Five high-contrast metric cards highlighting:
  - **Total Findings**: Aggregate vulnerability count.
  - **Critical**: Unauthenticated RCE, hardcoded production secrets, SQLi.
  - **High**: SSRF, command injection, insecure deserialization.
  - **Medium**: XSS, broken cryptography, missing authorization.
  - **Low**: Information disclosure, deprecated methods, minor syntax warnings.

### 5. Filterable Findings Table (`FindingsTable.jsx`)
- Sortable and filterable by severity, category, and file name.
- Search input for real-time finding filtering.
- Expanding row triggers the detailed finding drawer showing:
  - Precise line numbers (`auth.py:L42-L58`).
  - Grounded CWE citation badges linking to MITRE advisories.
  - Natural-language reasoning synthesized by the agent.

### 6. Intelligent Code Diff Engine & Token-Level Highlighting (`DiffViewer.jsx`)
- **Longest Common Subsequence (LCS) Line Diffing**:
  - Compares original code and replacement patch line-by-line rather than blanket-coloring entire code blocks.
  - Unchanged lines remain in neutral syntax gray (`text-gray-400`), receding into the background.
  - Removed/modified lines are highlighted with high-contrast rose banners (`bg-rose-950/40 border-l-4 border-rose-500`).
  - Added/replacement lines are highlighted with emerald green banners (`bg-emerald-950/40 border-l-4 border-emerald-500`).
- **Word / Token-Level In-Line Highlight**:
  - For modified lines, isolates the exact differing identifier (e.g., `innerHTML` vs `textContent`) using prefix/suffix analysis and renders prominent token pills (`bg-rose-900` / `bg-emerald-800`).
- **Interactive Controls & Productivity Tools**:
  - **Change Statistics**: Header pills displaying exact line alterations (`-1 line`, `+2 lines`).
  - **Jump to Change**: One-click target button that smooth-scrolls directly to the first modified line.
  - **Focus Mode ("Changes Only")**: Collapses unchanged boilerplate code and isolates changed lines within a configurable context window (`@@ N unchanged lines hidden @@`).
  - **Dual Display Modes**: Toggle between `Split (Side-by-Side)` and `Unified (Git Diff Stream)`.
  - **True Line Numbering**: Gutter reflects actual file line bounds (e.g., `L109–L142`) matching finding cards.
  - **Copy Replacement**: Seamless one-click clipboard action.

### 7. Interactive Dependency Call Graph (`DependencyFlow.jsx`)
- Built with React Flow (`@xyflow/react`).
- **Hierarchical Folder Architecture (Default View)**:
  - Intelligently collapses complex multi-thousand function graphs into clean, modular top-level directory nodes (e.g., `app/api`, `app/db`, `alembic`, `(root)`).
  - Cross-folder edges depict aggregated architectural dependencies with invocation weights and animated flows.
  - Folder node borders and glow rings dynamically indicate aggregate security posture: Red/Rose for Critical/High findings, Amber for Medium, and Emerald for Clean.
- **Interactive 2-Level Drilldown Modal**:
  - **Level 1 (Folder Overview)**: Clicking any folder node opens a sleek slide-in/modal displaying:
    - Connected dependencies ("Calls into...", "Called by...").
    - Search filter across all files in that directory.
    - Card grid of files with their individual function counts and risk badges.
  - **Level 2 (File Deep Dive)**: Clicking any file card transitions to a breadcrumb-backed view (`Map > 📁 Folder > 📄 File`):
    - Function search filter and list of all functions with exact line bounds (`L42–L58`).
    - Embedded Vulnerability Diffs: Functions with findings display the CWE alert, original vulnerable code, and verified AI remediation with one-click "Copy Fix".
- **Dual View Modes**: Seamless toggle between `📁 Folders Architecture` (clean high-level design) and `🌐 Micro-Graph` (complete raw function node network).
