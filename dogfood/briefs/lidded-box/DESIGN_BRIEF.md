+++
project_name = "lidded-box"
summary      = "A parametric friction-fit lidded box: a rectangular tray and a press-on lid."
units        = "mm"
components   = ["box", "lid"]

[coordinate_system]
x = "box width, left-to-right along the longer footprint edge"
y = "box depth, front-to-back along the shorter footprint edge"
z = "vertical, up; the box floor sits on the build plate at z = 0"

[[parameters]]
name    = "inner_width"
meaning = "interior cavity size along X"
default = 80.0
cli     = true

[[parameters]]
name    = "inner_depth"
meaning = "interior cavity size along Y"
default = 55.0
cli     = true

[[parameters]]
name    = "inner_height"
meaning = "interior cavity depth along Z, from floor to box rim"
default = 40.0
cli     = true

[[parameters]]
name    = "wall_thickness"
meaning = "thickness of the four box side walls"
default = 2.4
cli     = false

[[parameters]]
name    = "floor_thickness"
meaning = "thickness of the box floor slab"
default = 2.0
cli     = false

[[parameters]]
name    = "lid_top_thickness"
meaning = "thickness of the lid's flat top panel"
default = 2.0
cli     = false

[[parameters]]
name    = "lid_lip_height"
meaning = "how far the lid's inner lip descends into the box mouth"
default = 8.0
cli     = false

[[parameters]]
name    = "lid_lip_thickness"
meaning = "wall thickness of the lid's downward-projecting friction lip"
default = 1.6
cli     = false

[[parameters]]
name    = "fit_clearance"
meaning = "per-side gap between the lid lip and the box inner wall for the friction fit"
default = 0.15
cli     = true

[[parameters]]
name    = "lid_overhang"
meaning = "how far the lid skirt extends past the box outer wall on each side"
default = 1.5
cli     = false

[[parameters]]
name    = "corner_fillet"
meaning = "rounding radius applied to the vertical outer corners"
default = 3.0
cli     = false
+++

# Design Brief — lidded-box

A small parametric storage box with a press-on, friction-fit lid. Two artifacts
build from one script: the `box` (an open-top tray) and the `lid` (a capping
panel with a downward lip that grips the box's inner walls). The default size is
a desk-drawer organizer roughly 85 x 60 x 44 mm overall.

## 1. Context & assembly

The part is a general-purpose container — think small-parts storage, a drawer
divider cup, or a gift box. It assembles from exactly two printed pieces and no
fasteners: the `lid` presses onto the `box`.

The box is an open-top tray: a floor slab plus four walls. Its interior cavity
is `inner_width` x `inner_depth` x `inner_height`; outer footprint is the cavity
inflated by `wall_thickness` on each side. The walls rise to a flat rim at
z = `floor_thickness + inner_height`.

The lid has three features stacked in Z: a flat top panel (`lid_top_thickness`),
a short outer skirt that overhangs the box rim by `lid_overhang` on every side
(so the closed lid is easy to grip and pull), and an inner **friction lip** that
projects downward into the box mouth. The lip is what holds the lid on: its
outer face sits `fit_clearance` inside the box's inner wall on every side, so it
wedges against the wall when pressed home. `lid_lip_height` sets how deep the
lip reaches; `lid_lip_thickness` sets the lip's own wall thickness.

The mating interface is the box inner wall against the lid lip outer wall. The
controlling relationship: `lid lip outer dimension = inner cavity dimension -
2 * fit_clearance`, in both X and Y.

## 2. Tolerances & fits

- **Friction fit, lid-to-box.** `fit_clearance` (default 0.15 mm per side) is
  the single fit knob. It is exposed on the CLI because the right value depends
  on printer, filament, and how tight a grip is wanted. Tune it by printing the
  lid alone at a few values: smaller is tighter.
- 0.10-0.15 mm per side is a snug, deliberate press fit on a well-calibrated
  FDM printer. 0.20-0.30 mm per side gives a loose lid that lifts off easily.
  Negative or zero clearance will not assemble.
- `wall_thickness` 2.4 mm and `lid_lip_thickness` 1.6 mm are both multiples
  convenient for a 0.4 mm nozzle (6 and 4 perimeters respectively), giving solid
  walls with no sparse infill in the thin sections.
- The lip is intentionally thinner than the box wall so the lip — not the box —
  flexes slightly during the press, keeping the box rim dimensionally stable.

## 3. Print constraints

- **Orientation.** Both parts print flat on the build plate, no supports. The
  box prints floor-down, walls rising in Z. The lid prints top-panel-down so the
  lip points up — the lip's interior is then a simple open channel, not an
  overhang.
- **No bridging.** Neither part bridges. The box is open-topped; the lid's
  features are all walls rising from a solid panel.
- **First layer.** The box floor and the lid top each form a wide first layer —
  ensure good bed adhesion or a brim if warping appears at the corners.
- `corner_fillet` (3 mm) rounds the four vertical outer corners. This is
  cosmetic and reduces sharp-corner warping; it is not a functional fit feature.
- Thin-feature note: `lid_lip_thickness` 1.6 mm and `floor_thickness` 2.0 mm are
  the smallest dimensions in the model; do not reduce them below ~1.2 mm without
  re-checking perimeter counts.

## 4. Named size presets

None. The box is fully parametric and not tied to any known-model dimensions;
size it directly via `--inner-width`, `--inner-depth`, and `--inner-height`.

## 5. Verification approach

There are no automated tests. Verify by:

- **Bounding-box sanity check** on the exported STL. With default parameters the
  `box` outer footprint is `inner_width + 2*wall_thickness` x
  `inner_depth + 2*wall_thickness` = 84.8 x 59.8 mm, and overall height
  `floor_thickness + inner_height` = 42.0 mm. The `lid` outer footprint is the
  box footprint plus `2*lid_overhang` = 87.8 x 62.8 mm.
- **Re-slicing in Bambu Studio** to confirm both parts print without supports in
  the orientations above.
- **Physical fit check:** print the `lid` and `box`, press them together, and
  confirm the friction fit holds the lid but still releases by hand. Adjust
  `--fit-clearance` and reprint the lid only if needed.

## 6. Reference sketches

None attached for this example. A useful sketch would be a front-section view
showing the box wall, the lid lip nested inside it, and the `fit_clearance` gap
called out between them.

## 7. Out of scope / non-goals

- No hinge, latch, or snap-fit detents — the lid is held by friction alone.
- No internal dividers or compartments; the cavity is a single open volume.
- No stacking or interlocking features between multiple boxes.
- No gasket, seal, or any claim of being watertight or airtight.
- No text, logos, or embossed labels on any face.

## 8. Open questions

- Should the lid top carry a recessed finger-pull or grip texture to make
  opening easier? Deferred — the `lid_overhang` skirt is the v1 grip.
- Is a chamfer on the lip's leading edge wanted to ease starting the press?
  Likely yes for production; left out of the initial parameter set to keep the
  brief minimal.
- Should `wall_thickness` become a CLI flag too? Kept fixed for now since the
  2.4 mm value is nozzle-tuned; revisit if a thinner-walled variant is needed.
