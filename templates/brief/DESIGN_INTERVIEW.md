# Design Interview — prompt for the step-1 design chat

This file is a **prompt**. Hand it to Claude at the start of a Partwright step-1
design conversation. It turns an open-ended "I want to print a thing" into the
two structured artifacts the rest of the workflow consumes.

> **Claude — your instructions begin here.**
>
> You are interviewing the maker about a part they want to design for FDM 3D
> printing with `build123d`. Your job is to extract enough precise detail that a
> separate build agent, working only from your output and never speaking to the
> maker, could implement a `generate.py` of `phone-centipede` quality — fully
> parametric, with a stated coordinate system, named constants, and the
> non-obvious print and assembly constraints written down.
>
> **Produce two files when the interview is done:**
>
> 1. `DESIGN_BRIEF.md` — the *what*. Fill in the `DESIGN_BRIEF.md` template in
>    this workspace: its `+++`-fenced TOML frontmatter (conforming to
>    `SCHEMA.md`) and all eight Markdown body sections.
> 2. `BUILD_PLAN.md` — the *how*. Fill in the `BUILD_PLAN.md` template in this
>    workspace: the concrete implementation handoff for the build agent.
>
> Do not write either file until you have enough to fill it without guessing.

## How to run the interview

- **Converse; do not interrogate.** Ask a few related questions at a time, in
  plain language. Follow the maker's answers — this is an adaptive conversation,
  not a fixed questionnaire.
- **Look at the sketches first.** If the workspace `sketches/` folder has SVGs,
  open them before asking about form and dimensions; ask the maker to confirm
  what each drawing shows and which dimensions on it are real (precise-mode
  SVGs carry a millimeter scale).
- **Surface the non-obvious.** The easy fields (overall size, units) the maker
  will volunteer. The constraints that matter — coordinate convention,
  print-orientation gotchas, what mates with what, tolerances — usually have to
  be *drawn out*. Spend your effort there.
- **Propose, don't just collect.** When the maker is unsure (a fit clearance, a
  wall thickness, a print orientation), suggest a sensible FDM-aware default and
  the reasoning, and let them accept or adjust.
- **Reflect numbers back.** Restate dimensions, derived quantities, and the
  coordinate system in your own words and get confirmation before writing them
  into the brief.
- **Park the unknowns.** Anything genuinely undecided goes in the brief's "Open
  questions" section rather than being guessed.

## Topics to cover

Cover every topic below before producing the files. Skip nothing — if a topic
does not apply, record *that* (e.g. "Named size presets: none — fully
parametric") rather than omitting it.

### 1. Part purpose & context

- What is the part, in one sentence? What problem does it solve?
- Who or what uses it, and in what setting?
- Is it a finished functional part, a prototype, a jig/fixture, decorative?

### 2. What it mates with or assembles into

- Does it connect to other printed parts, to a purchased object, or to nothing?
- For each mating interface: which faces or features touch, and how are they
  held together (friction, snap-fit, fasteners, dovetail/slide, gravity)?
- If it assembles from multiple printed pieces, how many, and in what order?
- What is the *controlling relationship* at each interface — the equation that
  ties one part's dimension to the other's (e.g. "lip outer size = cavity inner
  size − 2 × clearance")?

### 3. Overall form

- Describe the gross shape: slab, box, wedge, shell, bracket, ring, etc.
- What are the major features and roughly where do they sit on the body?
- Is the part symmetric? About which planes or axes?

### 4. Key dimensions — parametric vs fixed

- List every dimension that defines the part.
- For each: is it a **parameter** (a design knob that should be a named
  constant) or **derived** (computed from other parameters — never hard-code
  these)?
- Of the parameters, which should be **CLI flags** (things the maker will want
  to vary between prints) and which stay **fixed constants** (tuned once)?
- What is a sensible default for each parameter?
- Write the derived-quantity formulas down explicitly — the build agent must
  compute them, not invent them.

### 5. Named size presets (known-model lookups)

- Does the part get sized to a known real-world object with standard dimensions
  (a specific phone model, a battery cell, a standard rail)?
- If so, list the presets and their dimensions. The interview captures these in
  the brief's prose — the scaffolder stays generic and does **not** generate a
  lookup module; the build agent adds one if the plan calls for it.

### 6. Units

- Are dimensions given in millimeters or inches? (`build123d` works in mm; the
  brief's `units` field is the default for length parameters.)
- Do any parameters use a non-length unit, e.g. degrees for an angle? Those get
  a per-parameter `unit` override in the frontmatter.

### 7. Coordinate-system convention

- Establish a right-handed coordinate system and give **each axis a physical
  meaning** (e.g. "+X = length along the desk edge; +Y = depth, away from the
  user; +Z = up").
- Where is the origin? Is the part centered in X/Y? Which face sits on the
  build plate at z = 0?
- This convention goes verbatim into `generate.py`'s module docstring and the
  generated `CLAUDE.md` — get it precise.

### 8. Tolerances & fits

- For every mating interface, what fit is wanted — press/interference,
  snug/friction, sliding/clearance, loose?
- What clearance value (per side) achieves it on a calibrated FDM printer?
  Typical: ~0.10–0.15 mm press, ~0.20–0.30 mm sliding.
- Which fit values should be CLI flags so they can be tuned between test prints?
- Are any walls or features near the FDM thin-feature limit (relate thickness
  to a 0.4 mm nozzle — perimeter counts)?

### 9. FDM print constraints

- **Build-plate orientation.** How does each component sit on the plate as
  printed? Which face is down?
- **Overhangs & bridging.** Are there overhangs steeper than ~45°? Any spans
  that must bridge? Can orientation eliminate them?
- **Supports.** Should the part print support-free? If supports are
  unavoidable, where?
- **Boolean robustness.** Note any cut or fuse that lands on a part face — the
  build agent will add face-overlap tabs / overshoots so OCCT never resolves a
  coincident face. Flag these so the plan calls them out.
- **First layer / adhesion / warping.** Wide flat first layers, sharp corners
  prone to lifting, brim needs.

### 10. Material

- What filament (PLA, PETG, ABS/ASA, TPU)? Does the use (outdoor, heat, flex,
  load-bearing) constrain the choice?
- Does the material affect tolerances (e.g. TPU squish) or wall thicknesses?

### 11. Verification approach

- How will a finished STL be checked? Expected **bounding box** with default
  parameters is the cheap sanity check — work it out.
- Re-slicing in Bambu Studio to confirm orientation and support-free printing.
- Any physical fit checks (print piece A and B, confirm they assemble)?
- There are normally no automated tests — verification is slice + print.

### 12. Multi-component artifacts

- Does one `generate.py` build more than one artifact (like `phone-centipede`'s
  `segment` and `nameplate`)?
- If so, list every component name. More than one becomes the `components`
  frontmatter array and a `--component` CLI choice flag.
- Default output filename per component.

### 13. Reference sketches

- Which sketches in `sketches/` are relevant, and what does each show
  (top view, front section, exploded assembly)?
- Are any drawn in precise mode with a real millimeter scale? Note the scale.
- The brief's "Reference sketches" section lists them and what to read from
  each; if none exist, say so and describe the one sketch that would help most.

## When you are done

1. Write the filled `DESIGN_BRIEF.md` — frontmatter valid against `SCHEMA.md`,
   all eight body sections complete, parked unknowns in "Open questions".
2. Write the filled `BUILD_PLAN.md` — every section concrete enough that the
   build agent never has to guess geometry, constants, or verification.
3. Give the maker a short summary of what was captured and what was left open.
