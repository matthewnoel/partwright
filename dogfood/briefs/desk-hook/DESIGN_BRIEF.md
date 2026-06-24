+++
project_name = "desk-hook"
summary      = "An under-shelf S-hook that clamps over a shelf edge to hang a bag or headphones."
units        = "mm"
components   = ["hook"]

[coordinate_system]
x = "width of the hook, across the shelf edge"
y = "depth, the direction the shelf edge runs away from the hanging load"
z = "vertical, up; the hanging arm descends in -Z and the part's lowest point sits at z = 0"

[[parameters]]
name    = "shelf_thickness"
meaning = "thickness of the shelf the hook clamps over, sets the throat gap"
default = 25.0
cli     = true

[[parameters]]
name    = "hook_width"
meaning = "width of the hook body along X"
default = 18.0
cli     = true

[[parameters]]
name    = "arm_thickness"
meaning = "wall thickness of every arm of the S profile"
default = 4.0
cli     = false

[[parameters]]
name    = "throat_clearance"
meaning = "extra gap added to shelf_thickness so the hook slides on without forcing"
default = 0.4
cli     = true

[[parameters]]
name    = "hang_drop"
meaning = "how far the front hanging arm descends below the shelf underside"
default = 35.0
cli     = false

[[parameters]]
name    = "lip_height"
meaning = "height of the small retaining lip at the bottom of the hanging arm"
default = 8.0
cli     = false

[[parameters]]
name    = "corner_fillet"
meaning = "rounding radius on the outer corners of the S bends"
default = 3.0
cli     = false
+++

# Design Brief — desk-hook

A single-piece S-hook that hangs off the edge of a shelf or desk top. The top
bend clamps over the shelf; the front arm drops down and ends in a small upturned
lip that keeps a bag strap or headphone band from sliding off.

## 1. Context & assembly

One printed part, no fasteners. The profile is an S laid on its side: a top
horizontal arm sits on the shelf, a back arm drops behind the shelf edge, and a
front arm drops in front of it. The throat between the front and back arms is
`shelf_thickness + throat_clearance` so the hook slides onto the shelf with a
light friction grip. The hanging load sits in the lower curve of the front arm,
retained by `lip_height`.

The part is extruded along X by `hook_width`; all the shaping happens in the
Y-Z profile.

## 2. Tolerances & fits

- **Slide fit over the shelf.** `throat_clearance` (default 0.4 mm) is the only
  fit knob and is on the CLI: increase it for a looser slide, decrease toward 0
  for a tighter grip. The hook relies on its own springiness plus gravity, so a
  snug-but-not-forced fit is ideal.
- `arm_thickness` 4.0 mm gives a stiff hook on a 0.4 mm nozzle (10 perimeters);
  do not drop below ~3.0 mm or the front arm will flex under load.

## 3. Print constraints

- **Orientation.** Print flat on one X face so the S profile is the layer
  outline — this makes every arm solid-perimeter and avoids supports entirely.
- No bridging in this orientation; the throat is an open notch, not a hole.
- `corner_fillet` softens the outer S bends, both cosmetic and stress-relieving.

## 4. Named size presets

None. Set `--shelf-thickness` to match the shelf; common values are 18 mm
(particleboard) and 25 mm (a thick desktop).

## 5. Verification approach

No automated tests. Verify by:

- **Bounding-box sanity check:** width equals `hook_width` (18 mm default);
  overall height is roughly `hang_drop` plus the throat depth.
- **Throat-gap check:** measure the front-to-back inner gap and confirm it equals
  `shelf_thickness + throat_clearance`.
- **Physical check:** slide it onto the target shelf and hang the intended load.

## 6. Reference sketches

None attached. A side-on profile sketch of the S with the throat gap dimensioned
would be the most useful reference.

## 7. Out of scope / non-goals

- No screw holes or permanent mounting — the hook is removable by design.
- No multi-hook rail; this is a single hook.
- No load rating claim beyond light bags and headphones.

## 8. Open questions

- Should the front arm carry a rubberized or textured pad to stop straps
  sliding? Deferred; the lip is the v1 retention.
- Is a CLI flag for `hang_drop` wanted for taller loads? Kept fixed for now.
