---
name: Predictive Maintenance Control Center
description: A restrained technical workspace for measured observations and model inference.
colors:
  primary-teal: "#48d3bd"
  analytical-blue: "#7cafff"
  analytical-amber: "#f4bd6a"
  observed-coral: "#ed8393"
  navy-ground: "#101722"
  charcoal-surface: "#192434"
  primary-text: "#e7edf5"
  secondary-text: "#b3c2d4"
  chart-text: "#cbd7e6"
  metric-divider: "#344458"
  selection-ground: "#23665e"
typography:
  headline:
    fontFamily: "sans-serif"
    fontSize: "2.15rem"
    letterSpacing: "-0.025em"
  headline-mobile:
    fontFamily: "sans-serif"
    fontSize: "1.7rem"
  title:
    fontFamily: "sans-serif"
    fontSize: "1.3rem"
  chart:
    fontSize: "13px"
spacing:
  compact: "1rem"
  workspace-top: "2rem"
  workspace-bottom: "3rem"
components:
  workspace:
    width: "1500px"
  caption:
    textColor: "{colors.secondary-text}"
  metric:
    padding: "1rem 0"
---

# Design System: Predictive Maintenance Control Center

## Overview

**Creative North Star: "Industrial analytical workspace"**

The user brief fixes a professional technical interface with navy and charcoal surfaces and
restrained teal or blue accents. Mode: Operate. Primary tasks are locating observations,
distinguishing recorded labels from model scores, and running inference. Flat analytical
content and native Streamlit controls carry the interface.

This record preserves the existing sidebar, wide workspace, responsive stacking and explicit
uncertainty. Values are extracted from `.streamlit/config.toml` and `src/ui.py`. No decorative
imagery or authored animation appears in the implementation.

**Key Characteristics:**

- Plain page titles and concise task descriptions.
- Measurements with explicit units and labeled states.
- Persistent desktop navigation and collapsible mobile navigation.
- Analytical charts, tables and provenance caveats.
- Readable full-opacity captions.

## Colors

Frontmatter owns the normative values. The palette uses a dark neutral ground, a distinct
secondary surface and restrained comparison colors.

### Primary

- **Primary teal:** native primary actions, selected controls, focus and chart series.

### Secondary

- **Analytical blue:** comparative series and nonfailure scatter points.
- **Analytical amber:** an additional comparison series.
- **Observed coral:** recorded-failure scatter points and the fourth comparison series.

### Neutral

- **Navy ground:** application canvas.
- **Charcoal surface:** sidebar and secondary surfaces.
- **Primary text:** ordinary interface text.
- **Secondary text:** interpretation, provenance and status captions.
- **Chart text:** chart labels and legends.
- **Metric divider:** fine rule beneath each metric.
- **Selection ground:** selected text background, paired with white text.

**The Readable Caveat Rule.** Captions use their explicit text color at full opacity.
The original framework dimming reduced essential caveat contrast and is not part of the system.

## Typography

**Display and body font:** Streamlit's bundled sans-serif system, selected through its theme.
No external font request is required. Exact framework font weights and line-heights remain
framework-owned rather than being invented as project tokens.

### Hierarchy

- **Headline:** page h1 uses the headline token with compact negative tracking.
- **Mobile headline:** the smaller headline token applies at the authored mobile breakpoint.
- **Title:** h2 uses the title token, with additional space above sections.
- **Body and controls:** native Streamlit typography preserves recognizable affordances.
- **Chart labels:** compact chart typography with explicit measurement labels.
- **Metric values:** tabular numerals support stable numerical comparison.

## Layout

The wide workspace has a maximum width of 1500px, workspace-top padding and workspace-bottom
padding. At a maximum viewport width of 640px, top padding becomes compact and the mobile
headline token applies. Native columns stack on narrow screens; mobile captures show no
document-level overflow. Tables retain native scrolling where necessary.

A sidebar contains four task destinations and current model/status information. Its native
collapse control provides mobile navigation. Page titles and descriptions lead the main
workspace. Filters precede desktop metric strips. Paired charts use equal columns; registers
span available width. Manual prediction groups measurements in two columns.

Charts fill their containers at a consistent height of 340px, with transparent paper/plot
backgrounds, compact margins and horizontal legends. These are chart conventions, not a
requirement for identical page composition.

## Elevation & Depth

The authored interface is flat. Navy and charcoal establish tonal separation, while thin
rules organize metrics. No custom shadow or glow vocabulary is defined. Native popovers,
menus and control borders retain framework behavior.

## Shapes

Native Streamlit fields, buttons, tabs and form boundaries keep their rounded framework
geometry. The project defines no radius scale. Metrics are open content blocks with bottom
rules, not decorative nested cards.

## Components

### Buttons and focus

Prediction uses a native primary button; downloads and explicit cloud checks use secondary
controls with action names. Focus-visible targets receive a primary-teal outline (2px) with
a 3px offset. Native hover, loading and disabled states remain framework-owned.

### Inputs and filters

Select, multiselect, text and numeric fields keep visible labels. Measurement labels include
units. Training ranges appear in help. Invalid, unavailable, empty and out-of-range states
use explicit text and recovery guidance. Filter chips inherit native selected treatment.

### Metrics and captions

Metrics use compact vertical padding, tabular numerals and a 1px bottom divider. Captions
remain full-opacity even when describing uncertainty or unavailable integrations.

### Navigation

Four native sidebar links share space with model and artifact status. Streamlit provides
the active destination treatment. The application entrypoint owns routing; modules live in
`views/` to avoid legacy page auto-discovery bypassing the shared shell.

A native sidebar radio selects High precision or Balanced F1 classification. Probability
estimates stay fixed while the selected threshold and category change. Manual results label
the last submitted observation, and tables identify estimated failure probability on a 0–1 scale.

### Charts and registers

Plotly uses the recorded four-series palette, transparent backgrounds, explicit axes and
horizontal legends. Recorded-failure scatter colors are explicitly mapped. Charts are
accompanied by downloadable data or tables. Series colors are not industrial risk standards.

## Do's and Don'ts

### Do:

- **Do** preserve the user's navy/charcoal technical direction and restrained accents.
- **Do** keep measured labels, model scores, partitions and units explicit.
- **Do** retain readable captions, native keyboard access and narrow-screen stacking.
- **Do** substantiate analytics with real tables, charts and downloadable data.

### Don't:

- **Don't** communicate observed failure or risk category through color alone.
- **Don't** present historical observations as live sensors or unique machines.
- **Don't** style an uncalibrated score as a guaranteed probability or safety standard.
- **Don't** invent radius, shadow, motion or typography scales absent from the implementation.
