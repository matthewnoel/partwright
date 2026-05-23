# Build Plan — lidded-box

The implementation handoff for the step-2 build agent. It turns the
`DESIGN_BRIEF.md` (the *what*) into a concrete plan for `generate.py` (the
*how*). The goal is a single-file `build123d` CLI of `phone-centipede` quality.

## Objective

A single-file `generate.py` that emits STLs for a parametric friction-fit
lidded box. Two artifacts, selected by `--component`:

- `box` (default) — an open-top rectangular tray.
- `lid` — a press-on cap with a downward friction lip.

Both must run out of the box with default parameters and produce valid STLs.

## Geometry approach

Coordinate system (right-handed), as stated in the brief:

- **+X** — box width, the longer footprint edge.
- **+Y** — box depth, the shorter footprint edge.
- **+Z** — vertical, up. The box floor and the printed lid both sit on the
  build plate at z = 0.

Everything is centered in X and Y. State this convention in the `generate.py`
module docstring and in `CLAUDE.md`.

### `box`

1. Build the outer solid: a `Box` of
   `(inner_width + 2*wall_thickness)` x `(inner_depth + 2*wall_thickness)` x
   `(floor_thickness + inner_height)`, sitting on z = 0.
2. Apply `corner_fillet` to the four vertical outer edges.
3. Cut the cavity: a `Box` of `inner_width` x `inner_depth` x `inner_height`,
   positioned so its bottom face is at z = `floor_thickness` and it is open at
   the top. Give the cutter a small upward overshoot above the box rim so the
   Boolean never resolves a face coincident with the top face (see
   boolean-robustness note below).

### `lid`

Model the lid in its **printed** orientation — top panel down, lip pointing up,
so it sits on the build plate as printed. (If modeling top-up is more natural,
mirror or rotate before export; the exported STL must be print-ready.)

1. Outer skirt + top panel: a `Box` of
   `(box_outer_width + 2*lid_overhang)` x `(box_outer_depth + 2*lid_overhang)` x
   `(lid_top_thickness)` for the top panel, where `box_outer_width` and
   `box_outer_depth` are the box outer footprint. Apply `corner_fillet` to the
   vertical outer edges to match the box.
2. Friction lip: a hollow rectangular wall projecting from the underside of the
   top panel. Its outer footprint is
   `(inner_width - 2*fit_clearance)` x `(inner_depth - 2*fit_clearance)`; its
   wall thickness is `lid_lip_thickness`; its height is `lid_lip_height`. Build
   it as an outer `Box` minus an inner `Box`.
3. Fuse the lip to the top panel, with a small overlap at the joint face so the
   Boolean is robust.

### Derived quantities (compute, do not hard-code)

- `box_outer_width  = inner_width + 2*wall_thickness`
- `box_outer_depth  = inner_depth + 2*wall_thickness`
- `box_outer_height = floor_thickness + inner_height`
- `lid_outer_width  = box_outer_width + 2*lid_overhang`
- `lid_outer_depth  = box_outer_depth + 2*lid_overhang`
- `lip_outer_width  = inner_width - 2*fit_clearance`
- `lip_outer_depth  = inner_depth - 2*fit_clearance`

## Constants to define

Named constants at the top of `generate.py`, grouped with section banners.
From the brief's `[[parameters]]` (units are mm unless noted):

| Constant | Default | CLI flag | Notes |
| --- | --- | --- | --- |
| `INNER_WIDTH_MM` | 80.0 | `--inner-width` | interior cavity X |
| `INNER_DEPTH_MM` | 55.0 | `--inner-depth` | interior cavity Y |
| `INNER_HEIGHT_MM` | 40.0 | `--inner-height` | interior cavity Z |
| `WALL_THICKNESS_MM` | 2.4 | — | side wall thickness |
| `FLOOR_THICKNESS_MM` | 2.0 | — | box floor thickness |
| `LID_TOP_THICKNESS_MM` | 2.0 | — | lid top panel thickness |
| `LID_LIP_HEIGHT_MM` | 8.0 | — | lip descent into the box |
| `LID_LIP_THICKNESS_MM` | 1.6 | — | lip wall thickness |
| `FIT_CLEARANCE_MM` | 0.15 | `--fit-clearance` | per-side friction gap |
| `LID_OVERHANG_MM` | 1.5 | — | skirt overhang past the box wall |
| `CORNER_FILLET_MM` | 3.0 | — | vertical outer corner radius |

Add a private boolean-robustness constant, e.g. `_FACE_OVERLAP_MM = 0.2`, for
cutter/fuser overshoot.

## CLI surface

`argparse`, mirroring `phone-centipede`:

- `--component {box,lid}` — which artifact to build; default `box`.
- `--inner-width FLOAT` — interior cavity size along X (mm).
- `--inner-depth FLOAT` — interior cavity size along Y (mm).
- `--inner-height FLOAT` — interior cavity depth along Z (mm).
- `--fit-clearance FLOAT` — per-side lid-to-box friction gap (mm).
- `--output PATH` — STL output path. Default: `lidded-box.stl` for the box,
  `lidded-box-lid.stl` for the lid.

Each flag's help text comes from the matching parameter's `meaning`. Only the
parameters with `cli = true` in the brief get flags; the rest stay constants.

## File layout

- `generate.py` — the single-file CLI (shebang, module docstring with the
  coordinate system, constants block, geometry helpers, assembly section,
  `argparse` CLI, `main()`).
- `CLAUDE.md` — guidance: what this is, coordinate system, Python-env caveat,
  `black` code style, boolean-robustness conventions, a "non-obvious geometry
  decisions" section to grow over time, and a pointer to this `BUILD_PLAN.md`.
- `README.md`, `requirements.txt` (`build123d==0.9.1`), `requirements-dev.txt`,
  `.gitignore`, `.claude/settings.local.json` — standard scaffolded files.

## Verification steps

1. `generate.py` runs with no arguments and writes `lidded-box.stl`.
2. `generate.py --component lid` writes `lidded-box-lid.stl`.
3. Bounding-box check, default parameters:
   - box: X 84.8 mm, Y 59.8 mm, Z 42.0 mm.
   - lid: X 87.8 mm, Y 62.8 mm, Z `lid_top_thickness + lid_lip_height` =
     10.0 mm.
4. `black generate.py` leaves the file unchanged.
5. Slice both STLs in Bambu Studio; confirm no supports needed in the printed
   orientations (box floor-down, lid top-panel-down).
6. Print both; confirm the lid presses on and holds by friction, and releases
   by hand. Tune `--fit-clearance` and reprint the lid only if needed.

## Boolean-robustness conventions

OCCT booleans are flaky when an operation must resolve two coincident faces; the
artifacts only show up after STL export. Avoid it:

- The cavity cutter and the lid-lip inner cutter extend slightly beyond the face
  they break through (`_FACE_OVERLAP_MM` overshoot), so no cut resolves a
  coincident face.
- When fusing the lip to the lid top panel, overlap the joint by
  `_FACE_OVERLAP_MM` rather than butting faces exactly.

## Known risks

- **Fit clearance is the whole design.** Too small and the lid will not seat;
  too large and it falls off. Treat `fit_clearance` as a tuning knob and expect
  one or two test prints of the lid.
- **Corner fillet vs. lip.** Keep `corner_fillet` applied only to the *outer*
  vertical edges. Filleting the cavity or lip corners changes the fit and is not
  intended.
- **Lid print orientation.** If the lid is modeled top-up, it must be flipped
  before export or it prints lip-down (an overhang). Verify the exported STL
  rests flat with the lip pointing up.
- **Thin features.** `lid_lip_thickness` 1.6 mm and `floor_thickness` 2.0 mm are
  the smallest walls; confirm the slicer assigns solid perimeters and no sparse
  infill there.
