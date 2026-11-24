---
name: Obsidian Executive
colors:
  surface: '#12131a'
  surface-dim: '#12131a'
  surface-bright: '#383941'
  surface-container-lowest: '#0d0e15'
  surface-container-low: '#1a1b22'
  surface-container: '#1e1f26'
  surface-container-high: '#292931'
  surface-container-highest: '#33343c'
  on-surface: '#e3e1ec'
  on-surface-variant: '#c8c5ca'
  inverse-surface: '#e3e1ec'
  inverse-on-surface: '#2f3038'
  outline: '#919095'
  outline-variant: '#47464a'
  surface-tint: '#c8c6c8'
  primary: '#c8c6c8'
  on-primary: '#313032'
  primary-container: '#09090b'
  on-primary-container: '#7a787b'
  inverse-primary: '#5f5e60'
  secondary: '#c8c6c9'
  on-secondary: '#303033'
  secondary-container: '#47464a'
  on-secondary-container: '#b6b4b8'
  tertiary: '#cec4c4'
  on-tertiary: '#352f2f'
  tertiary-container: '#0c0808'
  on-tertiary-container: '#7f7777'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e5e1e4'
  primary-fixed-dim: '#c8c6c8'
  on-primary-fixed: '#1c1b1d'
  on-primary-fixed-variant: '#474649'
  secondary-fixed: '#e4e1e5'
  secondary-fixed-dim: '#c8c6c9'
  on-secondary-fixed: '#1b1b1e'
  on-secondary-fixed-variant: '#47464a'
  tertiary-fixed: '#ebe0df'
  tertiary-fixed-dim: '#cec4c4'
  on-tertiary-fixed: '#1f1a1a'
  on-tertiary-fixed-variant: '#4c4545'
  background: '#12131a'
  on-background: '#e3e1ec'
  surface-variant: '#33343c'
typography:
  display:
    fontFamily: Manrope
    fontSize: 56px
    fontWeight: '600'
    lineHeight: 64px
    letterSpacing: -0.03em
  display-mobile:
    fontFamily: Manrope
    fontSize: 40px
    fontWeight: '600'
    lineHeight: 48px
    letterSpacing: -0.025em
  headline-lg:
    fontFamily: Manrope
    fontSize: 36px
    fontWeight: '600'
    lineHeight: 44px
    letterSpacing: -0.025em
  headline-lg-mobile:
    fontFamily: Manrope
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Manrope
    fontSize: 24px
    fontWeight: '500'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-sm:
    fontFamily: Manrope
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 28px
    letterSpacing: -0.01em
  title-md:
    fontFamily: Hanken Grotesk
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.005em
  body-lg:
    fontFamily: Hanken Grotesk
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 26px
    letterSpacing: 0em
  body-md:
    fontFamily: Hanken Grotesk
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
    letterSpacing: 0.005em
  body-sm:
    fontFamily: Hanken Grotesk
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Hanken Grotesk
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Hanken Grotesk
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.04em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 1rem
  margin: 3rem
  margin-mobile: 1.25rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

The design system embodies quiet luxury, restraint, and deliberate precision. Drawing direct lineage from Dieter Rams’ ethos of "less, but better" and refined Cupertino executive toolkits, it prioritizes clarity, structural integrity, and immaculate craftsmanship over decoration. 

The aesthetic is strictly monochromatic, minimal, and architectural. The interface recedes entirely, allowing user content, strategic insights, and mission-critical actions to command focus without distraction. There are no decorative badges, artificial glow filters, or superfluous decorative widgets. Depth is earned through spatial discipline, subtle perimeter definition, and refined typography.

Every touchpoint evokes composure, authority, and uncompromising quality.

## Colors

The palette is anchored in an ultra-deep obsidian and graphite spectrum. Surfaces avoid harsh pure black in favor of nuanced, dark mineral tones that deliver optimal OLED contrast while preventing visual fatigue.

- **Primary Canvas (`#09090B`)**: Deep obsidian base surface providing negative space and foundation.
- **Surface Elevation (`#121215`)**: Lifted graphite surface for structural panels, floating toolbars, and cards.
- **Subtle Perimeter Lines (`#27272A` / `#1F1F23`)**: Ultra-subtle structural lines defining layout hierarchy without adding visual weight.
- **Typography Primary (`#FFFFFF`)**: Pure optic white for immediate headline legibility, high-priority figures, and primary calls to action.
- **Typography Secondary (`#A1A1AA`)**: Neutral zinc for body copy and contextual descriptions.
- **Typography Tertiary (`#71717A`)**: Muted slate for metadata, disabled states, and unobtrusive axis labels.
- **System Accent (`#FAFAFA`)**: Reserved strictly for high-priority interactive states and key functional toggles.

## Typography

The pairing combines the geometric, architectural authority of **Manrope** for headlines with the clarity and neutrality of **Hanken Grotesk** for reading flows and micro-copy.

- **Tracking Philosophy**: Headlines employ negative letter-spacing to present a locked, sculpted typographic lockup. Labels and micro-data points utilize slight positive tracking to ensure high legibility at diminutive scales.
- **Rhythm & Line Height**: Generous line heights are maintained across body copy (`1.6x` ratio) to support sustained focus in high-density workflows.
- **Weights**: Restrained strictly to weights `400` (Regular), `500` (Medium), and `600` (Semi-bold). Avoid heavier display weights to sustain an airy, surgical feel.

## Layout & Spacing

The layout model relies on a calibrated 12-column grid system bounded by intentional, expansive negative space. Content breathes through disciplined whitespace increments derived from an 8-point base rhythm.

- **Desktop (1024px+)**: Max-width container of 1440px centered with `3rem` (48px) margins. Columns use `1.5rem` (24px) gutters. Functional sections are segregated by `space-xl` (40px) or `space-lg` (24px) margins.
- **Tablet (768px – 1023px)**: 8-column layout with `2rem` (32px) margins and `1.25rem` (20px) gutters. Multi-column grids compress logically (e.g., 4 columns collapse to 2).
- **Mobile (< 768px)**: 4-column layout with `1.25rem` (20px) margins and `1rem` (16px) gutters. Complex horizontal layouts collapse strictly into a linear vertical hierarchy.
- **Spatial Restraint**: Interfaces must avoid collapsing empty space to pack information. The void is an intentional visual separator that replaces decorative dividers and heavy containers.

## Elevation & Depth

This system rejects physical drop shadows, fuzzy glows, and multi-colored ambient lights. Elevation is communicated through two tactile techniques:

1. **Tonal Tiering**:
   - `Tier 0 (Base Canvas)`: `#09090B`
   - `Tier 1 (Structural Surfaces & Panels)`: `#121215`
   - `Tier 2 (Popovers, Modals & Floating Toolbars)`: `#18181B`

2. **Low-Contrast Precision Outlines**:
   - Depth between tiers is delineated using crisp 1px borders in `#27272A` or `#1F1F23`.
   - Modals and contextual overlays apply a fine border of `#27272A` accompanied by an ultra-diffused, black ambient occlusion mask (`rgba(0, 0, 0, 0.7)` backdrop blur with `backdrop-filter: blur(12px)`).

## Shapes

The shape system adopts a soft, architectural curvature that reflects vintage Braun equipment and machined slate finishes:

- **Base Radius (`roundedness: 1`)**: Standard elements like input fields, buttons, and chips use `0.25rem` (4px).
- **Surface Panels (`rounded-lg`)**: Larger groupings, structural cards, and data surfaces use `0.5rem` (8px).
- **Overlays (`rounded-xl`)**: Dialogs, sheets, and full modal containers use `0.75rem` (12px).
- **Form Geometry**: Corners are sharp enough to preserve disciplined grid structure, yet lightly eased to avoid raw digital harshness.

## Components

### Buttons
- **Primary**: Solid optic white background (`#FFFFFF`) with pure black text (`#09090B`), font weight `500`. Hover state gently dims opacity to `0.92`.
- **Secondary**: Elevated surface (`#121215`) with a 1px border (`#27272A`) and stark white text (`#FFFFFF`). Hover transitions border to `#3F3F46`.
- **Ghost**: Transparent background, text `#A1A1AA`. Hover shifts color to `#FFFFFF` with no background fill.
- **Dimensions**: Compact heights (`36px` to `40px`), padding `0 1rem`, `0.25rem` corner radius.

### Input Fields
- **Background**: `#09090B` or `#121215`.
- **Border**: 1px solid `#27272A`. Active focus transitions border to `#FAFAFA` with zero outer glow.
- **Typography**: Value text in `#FFFFFF`, placeholder text in `#71717A`.
- **Height**: Strictly `40px` with an internal padding of `0.75rem`.

### Cards & Panels
- **Structure**: Surface fill of `#121215` bordered by a 1px line of `#1F1F23`.
- **Padding**: Uniform `1.5rem` (`space-lg`) internal breathing room.
- **Dividers**: When dividing sections internally, utilize a 1px line of `#1F1F23` with no margins.

### Checkboxes & Radio Buttons
- **Unchecked**: 16px square/circle with 1px border `#27272A` on `#09090B`.
- **Checked**: Solid `#FFFFFF` fill with an interior `#09090B` check mark or center pip.
- **Interaction**: Crisp, instant transition with zero rubber-band or bouncy physics.

### Chips & Filter Tags
- **Default**: 1px border `#27272A`, background `#121215`, text `#A1A1AA`, height `28px`, padding `0 0.75rem`.
- **Active / Selected**: Border `#FAFAFA`, background `#18181B`, text `#FAFAFA`.

### Segmented Controls
- Continuous `#09090B` container with a 1px border (`#1F1F23`).
- Active segment elevated with surface `#18181B` and crisp `#FFFFFF` typography; inactive segments remain subdued in `#71717A`.