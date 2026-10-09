# Pixel Arcade Design System

A reusable visual and interaction system for digital products, studios, portfolios, campaigns, and other projects that want a confident retro-game feel. Treat this as a set of design rules, not a fixed page template: adapt the content, component selection, and brand voice to each project while keeping the visual language coherent.

## 1. Design intent

- **Character:** playful, crafted, direct, nostalgic, and technically capable.
- **Visual reference:** 8-bit / 16-bit games, arcade cabinets, pixel interfaces, command-line tools, and printed game manuals.
- **Core contrast:** near-black surfaces and warm off-white text, punctuated by arcade yellow.
- **Shape language:** square corners, visible outlines, pixel grids, stepped silhouettes, and offset hard shadows.
- **Tone:** confident and human. Keep copy concise, useful, and specific to the project.
- **Do not use:** generic SaaS styling, blurred glow, glassmorphism, soft gradients, purple/violet, or bright neon-blue lighting.

The system should feel deliberately pixel-inspired, not difficult to read or operate. Use pixel fonts selectively; use a crisp, readable monospace for most interface text.

## 2. Foundations

### Color palette

Use these as starting tokens. A project may introduce a restrained supporting color where its subject needs it, but preserve the dark / cream / yellow foundation and do not let supporting colors compete with the primary accent.

| Token | Hex | Purpose |
| --- | --- | --- |
| `color.ink` | `#0D0D0D` | Main page background and darkest text |
| `color.charcoal` | `#181818` | Alternate section and raised surface |
| `color.surface` | `#171716` | Cards, panels, and interactive surfaces |
| `color.surface-muted` | `#2A2A2A` | Secondary surface, separators, and muted blocks |
| `color.line` | `#333330` | Default borders and dividers |
| `color.cream` | `#F4F4F0` | Main text on dark surfaces |
| `color.yellow` | `#FFCC00` | Primary action, emphasis, active state, and indicators |
| `color.yellow-hover` | `#FFDB4D` | Yellow button hover surface |
| `color.text-muted` | `#9A9A91` | Secondary text on dark surfaces |
| `color.shadow` | `#000000` | Default offset shadow |

**Contrast and usage**

- Yellow is an accent, not a large-area default background. Use it for primary actions, emphasis, active states, small markers, and intentional highlight panels.
- Use cream for primary text on dark backgrounds. Use muted text for supporting information only; check that it remains legible at the rendered size.
- On a yellow surface, use ink or dark charcoal for text and icons.
- Borders should be visible and intentional. Avoid low-contrast hairlines on important controls.
- Do not communicate state using color alone; pair it with text, shape, or an icon.

### Typography

- **Display / arcade headings:** `Press Start 2P`, with a monospace fallback. Reserve this highly distinctive font for short headlines, section titles, tier names, and small labels.
- **Body / interface:** `DM Mono`, with a system monospace fallback. Use for paragraphs, navigation, controls, metadata, tags, and data.
- **Fallbacks:** `"Courier New", monospace`.
- Use a larger line height for pixel-font headings than for conventional display fonts. Break long headings into intentional short lines instead of shrinking them until they become hard to read.
- Avoid setting paragraphs, long descriptions, legal copy, or dense tables in the display font.
- Use all caps sparingly for compact labels, navigation, and calls to action. Sentence case is usually easier to scan for longer content.

Suggested type scale (adjust to the project and viewport):

| Role | Desktop | Mobile | Guidance |
| --- | --- | --- | --- |
| Display heading | `36–48px` | `24–34px` | Pixel font; use short deliberate lines |
| Section heading | `28–38px` | `22–30px` | Pixel font; clear hierarchy |
| Card title | `14–18px` | `13–17px` | Monospace or short pixel-font label |
| Body | `12–14px` | `11–13px` | Monospace; line height around `1.7–1.9` |
| Utility label | `8–10px` | `7–9px` | Monospace; keep readable and concise |

### Borders, shadows, and corners

- Prefer square corners. If a softer shape is needed for a particular asset (for example, a device mockup), keep the surrounding UI geometry square.
- Use crisp `1px` borders for quiet separation and `2px` borders for important components, controls, and panels.
- Use hard offset shadows with no blur:
  - Standard raised control: `4px 4px 0 #000`
  - Emphasized panel: `5px 5px 0 #735C00` or another dark, palette-compatible accent
  - Small control: `3px 3px 0 #000`
- Shadows should look like a physical, stepped offset, not a glow. Do not use blurred `box-shadow`.
- Keep outlines and shadow offsets consistent within a component family.

### Spacing and layout

Use a consistent spacing scale based on multiples of `4px`: `4, 8, 12, 16, 24, 32, 48, 64, 80, 112`.

- Center content in a readable container, typically `1120–1248px` wide.
- At desktop, use generous section separation (`80–112px` vertical padding).
- At mobile, reduce section separation to approximately `56–80px`.
- Keep card padding generous enough for text to breathe while preserving the compact arcade interface character.
- Use grids for collections and align edges between section headings, cards, and content.
- Avoid arbitrary narrow text columns that cause pixel headlines to wrap unpredictably.

## 3. Graphic language

- Build simple pixel marks from small square blocks, CSS grids, or crisp-edged SVGs.
- For SVG icons, use `shape-rendering: crispEdges` where appropriate and simple geometry that remains clear at small sizes.
- Use a small consistent icon set. Icons should support text, not replace necessary labels.
- Pixel-art decoration may include stars, status dots, scan grids, corner brackets, terminals, progress bars, or small sprites.
- Decorative sprites and visual noise must not cover text, controls, or important information.
- Keep illustrated or project-specific artwork modular: its color and subject may change while its crisp edges, high contrast, and deliberate pixel treatment remain consistent.
- Avoid random decoration. Give each visual element a purpose: hierarchy, status, brand recognition, or atmosphere.

## 4. Component rules

### Header and navigation

- Use a compact brand mark paired with a project-specific name or logo.
- Keep primary navigation short and easy to scan. Include only destinations relevant to the project.
- Give the primary navigation action a clear filled yellow treatment.
- On small screens, replace the inline navigation with a clearly labeled menu control and an accessible expanded/collapsed state.
- Keep sticky or fixed navigation optional; if used, account for its height in anchor scrolling and page layout.

### Buttons and links

- **Primary:** yellow fill, dark text, `2px` border, hard offset shadow.
- **Secondary:** transparent or dark fill, cream text, visible border, hard offset shadow.
- **Text link:** no button shell; use a clear hover/focus indicator and optional small directional icon.
- Hover may brighten a yellow fill or reveal a yellow outline. Active/pressed state should physically depress the control by moving it `2–3px` and reducing the shadow by a corresponding amount.
- Provide visible keyboard focus. Do not rely on hover or animation to disclose the action.
- Use descriptive labels that reflect the destination or action. Avoid making every link read like a game command.

### Cards and panels

- Use a charcoal or near-black surface, a crisp border, and consistent internal spacing.
- For hoverable cards, a small upward/diagonal shift and stronger yellow border/shadow are sufficient. Keep the effect quick and restrained.
- Make the whole card a link only when the card has one clear destination. Otherwise use a specific action link.
- Include tags, labels, or metadata only when they aid scanning or describe real content.
- Card layouts should remain useful when a title, image, description, or tag list is absent.

### Badges, tags, and data

- Render compact labels as outlined rectangular chips with readable text.
- Use yellow sparingly for the most important status or classification.
- Counters and achievements should use tabular or fixed-width numerals where possible to prevent layout shifts.
- Never imply a real metric, testimonial, client, price, or achievement with invented placeholder content in a shipped project. Replace demo copy with verified project-specific content.

### Forms and dialogs

- Match the border, surface, focus, and button rules of the rest of the system.
- Labels should remain visible when a field is filled. Placeholder text is not a label.
- Show validation and submission feedback in text, with appropriate semantic status roles.
- Keep form controls usable by keyboard and touch. Do not make pixel styling reduce hit targets.

## 5. Motion and interaction

- Motion should feel like a tiny arcade response: a short button press, a restrained sprite bob, a blinking terminal cursor, or a subtle status pulse.
- Prefer short transitions around `120–180ms`; use stepping for intentionally pixel-like sprite animation.
- Use animation to reinforce a state or add atmosphere, not to distract from content.
- Avoid flashing, rapid strobing, constant large movements, and parallax that can cause discomfort.
- Respect `prefers-reduced-motion: reduce`. Disable or substantially reduce non-essential movement and smooth scrolling.
- Provide equivalent focus and active feedback for keyboard and touch users.
- Ensure controls have a clear, immediate pressed state and sufficient touch area (ideally at least `44 × 44px`).



## 7. Accessibility and semantics

- Use semantic landmarks (`header`, `nav`, `main`, `section`, `footer`) and a logical heading order.
- Give each page one clear `h1`; section headings should use the next appropriate level.
- Use real links for navigation and real buttons for state changes.
- Give icon-only controls accessible names. Hide purely decorative icons and artwork from assistive technology.
- Maintain visible keyboard focus with sufficient contrast; never remove the browser outline without providing a replacement.
- Check text and control contrast on both dark and yellow surfaces.
- Do not convey meaningful status through a color, animation, or shape alone.
- Use meaningful alternative text for informative images. Use empty alternative text or hidden semantics for decorative images.
- Respect reduced-motion preferences and support keyboard operation throughout.

## 8. Content adaptation

Keep the style reusable by separating visual conventions from a particular industry or page outline.

- Replace business name, symbol, voice, navigation, section order, labels, and calls to action for each project.
- Select only the components needed by the project; there is no required agency, portfolio, pricing, or statistics section.
- Choose a project-specific secondary color only if it has a clear purpose and works with ink, cream, and yellow.
- Write headings for the project’s audience and use concrete descriptions instead of generic filler.
- Keep arcade terms (levels, quests, scores, coins) optional. Use them only when they support the project’s brand and user expectations.
- Use real prices, customer outcomes, badges, and social profiles, or omit them. Never present fabricated content as fact.
- Preserve the design language through typography, color roles, hard edges, and interaction feedback even when the information architecture changes.

## 9. Implementation guidance

The system can be implemented in React with CSS, CSS Modules, Tailwind theme tokens, or another component framework. Keep the design decisions in shared tokens and reusable components rather than copying one-off styles between pages.

Example CSS custom properties:

```css
:root {
  color-scheme: dark;
  --color-ink: #0d0d0d;
  --color-charcoal: #181818;
  --color-surface: #171716;
  --color-surface-muted: #2a2a2a;
  --color-line: #333330;
  --color-cream: #f4f4f0;
  --color-yellow: #ffcc00;
  --color-yellow-hover: #ffdb4d;
  --color-text-muted: #9a9a91;
  --font-display: "Press Start 2P", "Courier New", monospace;
  --font-body: "DM Mono", "Courier New", monospace;
  --shadow-raised: 4px 4px 0 #000;
  --shadow-accent: 5px 5px 0 #735c00;
  --border-strong: 2px solid var(--color-line);
  --content-width: 1120px;
}
```

Example pressed-button behavior:

```css
.button {
  border: 2px solid var(--color-yellow);
  background: var(--color-yellow);
  color: var(--color-ink);
  box-shadow: var(--shadow-accent);
  transition: transform 120ms ease, box-shadow 120ms ease;
}

.button:active {
  transform: translate(3px, 3px);
  box-shadow: 1px 1px 0 #735c00;
}

.button:focus-visible {
  outline: 2px solid var(--color-cream);
  outline-offset: 4px;
}
```

Implementation checklist:

- Define design tokens once and use them consistently.
- Build small, reusable primitives for buttons, tags, section headings, cards, and pixel icons.
- Keep project content and repeated lists in data modules where that fits the framework.
- Prefer crisp SVG/CSS pixel artwork; optimize raster artwork and provide meaningful alternatives.
- Avoid unnecessary JavaScript for decoration that CSS or SVG can handle.
- Validate production builds and manually inspect desktop, tablet, and mobile layouts.

## 10. Quality checklist

Before shipping a project using this system, verify:

- [ ] The page still reads as pixel/arcade-inspired without sacrificing clarity.
- [ ] The main palette remains ink, charcoal, cream, and yellow; there are no generic gradients or blurred glows.
- [ ] Pixel display type is reserved for short, high-impact text.
- [ ] Borders and shadows are crisp, square, and consistent.
- [ ] Buttons show hover, focus, and pressed feedback.
- [ ] Navigation and key actions work with keyboard, touch, and screen readers.
- [ ] Layout works at phone, tablet, and desktop widths with no horizontal overflow.
- [ ] Motion has a reduced-motion alternative and does not flash or distract.
- [ ] Project-specific facts and content are accurate; demo placeholders have been replaced or removed.
