# Build Plan — <part name>

The implementation handoff for the step-2 build agent. It turns the
`DESIGN_BRIEF.md` (the *what*) into a concrete plan for `generate.py` (the
*how*). The goal is a single-file `build123d` CLI of `phone-centipede` quality:
named constants at the top, a stated coordinate system, a deliberate CLI
subset, and the non-obvious decisions written down.

> Fill every section below. Where a section does not apply, say so explicitly
> rather than deleting it. The build agent works only from this file and the
> `DESIGN_BRIEF.md` — leave nothing to be guessed.

## Objective

<One paragraph: what `generate.py` produces. The artifact(s) it builds and,
if more than one, how `--component` selects between them. State that every
artifact must run out of the box with default parameters and emit a valid STL.>

## Geometry approach

State the coordinate system (right-handed), copied from the brief — give each
axis its physical meaning, the origin location, and which face sits on the
build plate at z = 0. This convention goes verbatim into the `generate.py`
module docstring and `CLAUDE.md`.

- **+X** — <meaning>
- **+Y** — <meaning>
- **+Z** — <meaning>

<State centering: e.g. "centered in X and Y; floor on z = 0".>

### <component / artifact name>

<Step-by-step construction of this artifact. Be concrete about build123d
operations — which primitives (`Box`, `Cylinder`, sketches + `extrude`,
`Polyline` + `make_face`), which Booleans (fuse / cut), and in what order.
Model each component in its PRINTED orientation so the exported STL is
print-ready; if a part is more natural to model another way, say to rotate or
mirror before export.>

1. <first construction step>
2. <next step>
3. <...>

<Repeat a `### <component name>` block for each artifact the part builds.>

### Derived quantities (compute, do not hard-code)

<Every quantity computed from the parameters, with its explicit formula. The
build agent must compute these — never hard-code a number that depends on
another. e.g.>

- `outer_width  = inner_width + 2 * wall_thickness`
- `<derived>    = <formula>`

## Constants to define

Named constants at the top of `generate.py`, grouped with section banners.
Derived directly from the brief's `[[parameters]]` blocks via the `SCHEMA.md`
naming rule (constant = NAME uppercased + unit suffix; flag = name with
hyphens). Units are the brief's `units` unless a row notes otherwise.

| Constant | Default | CLI flag | Notes |
| --- | --- | --- | --- |
| `OVERALL_LENGTH_MM` | 100.0 | `--overall-length` | <meaning> |
| `WALL_THICKNESS_MM` | 2.4 | — | <meaning> |
| `TILT_ANGLE_DEG` | 10.0 | `--tilt-angle` | <meaning> |
| `<CONSTANT>` | `<default>` | `<flag or —>` | <meaning> |

Add private boolean-robustness constants as needed, e.g.
`_FACE_OVERLAP_MM = 0.2`, for cutter/fuser overshoot (see below).

## CLI surface

`argparse`, mirroring `phone-centipede`. Only parameters with `cli = true` in
the brief get flags; the rest stay constants.

- `--component {<a>,<b>}` — which artifact to build; default `<a>`.
  *(Only if the brief lists more than one component.)*
- `--<flag> <TYPE>` — <help text, from the parameter's `meaning`>.
- `--output PATH` — STL output path. Default: `<project_name>.stl`
  (and `<project_name>-<component>.stl` per extra component).

<Note any input conversion, e.g. an `--units` flag that converts typed values
to mm, as `phone-centipede` does.>

## File layout

- `generate.py` — the single-file CLI: shebang, module docstring (with the
  coordinate system), named-constants block, geometry-helpers section,
  assembly section, `argparse` CLI, `main()`.
- `CLAUDE.md` — guidance: "What this is", coordinate system, Python-env caveat,
  `black` code style, boolean-robustness conventions, a "non-obvious geometry
  decisions" section to grow over time, and a pointer to this `BUILD_PLAN.md`.
- `README.md`, `requirements.txt` (`build123d==0.9.1`), `requirements-dev.txt`,
  `.gitignore`, `.claude/settings.local.json` — standard scaffolded files.
- <any extra module, e.g. a known-model lookup table — only if the plan calls
  for one.>

## Verification steps

1. `generate.py` runs with no arguments and writes `<project_name>.stl`.
2. <each `--component` invocation writes its expected STL.>
3. **Bounding-box check**, default parameters — the cheap sanity check:
   - <component>: X <value> mm, Y <value> mm, Z <value> mm.
4. `black generate.py` leaves the file unchanged.
5. Slice the STL(s) in Bambu Studio; confirm the printed orientation needs no
   supports.
6. <any physical fit check: print pieces, confirm they assemble; tune the
   CLI fit flag and reprint if needed.>

## Boolean-robustness conventions

OCCT Booleans are flaky when an operation must resolve two coincident faces;
the artifacts only surface after STL export. Avoid it:

- Cutters extend slightly **beyond** the face they break through
  (`_FACE_OVERLAP_MM` overshoot) so no cut resolves a coincident face.
- When fusing two solids, **overlap** the joint by `_FACE_OVERLAP_MM` rather
  than butting faces exactly.
- <Call out the specific cuts/fuses in this part that need this treatment.>

## Known risks

<The things most likely to go wrong, each with the failure mode and the
mitigation. Print-orientation gotchas, fits that need test prints, thin
features, Boolean-fragile geometry, anything the brief's "Open questions"
flagged. These become the seed of the repo's "non-obvious geometry decisions"
section in `CLAUDE.md` as fixes are discovered.>

- <risk> — <why it bites, and how to handle it>.
