+++
project_name = "pi-mount"
summary      = "A wall-mountable Raspberry Pi 4 baseplate with standoff bosses and keyhole slots."
units        = "mm"
components   = ["plate"]

[coordinate_system]
x = "plate width, along the long edge of the Pi board (the 85 mm dimension)"
y = "plate height, along the short edge of the Pi board (the 56 mm dimension)"
z = "vertical off the wall; the plate back sits at z = 0 and bosses rise in +Z"

[[parameters]]
name    = "board_hole_spacing_x"
meaning = "center-to-center distance between the Pi mounting holes along X"
default = 58.0
cli     = false

[[parameters]]
name    = "board_hole_spacing_y"
meaning = "center-to-center distance between the Pi mounting holes along Y"
default = 49.0
cli     = false

[[parameters]]
name    = "boss_outer_diameter"
meaning = "outer diameter of each standoff boss the Pi screws into"
default = 6.0
cli     = false

[[parameters]]
name    = "boss_height"
meaning = "how far each standoff boss lifts the board off the plate"
default = 4.0
cli     = true

[[parameters]]
name    = "boss_pilot_diameter"
meaning = "pilot hole in each boss for an M2.5 self-tapping screw"
default = 2.2
cli     = false

[[parameters]]
name    = "plate_margin"
meaning = "border of plate material around the board footprint on every side"
default = 6.0
cli     = false

[[parameters]]
name    = "plate_thickness"
meaning = "thickness of the baseplate slab"
default = 3.0
cli     = true

[[parameters]]
name    = "keyhole_diameter"
meaning = "diameter of the round entry of each wall-mount keyhole slot"
default = 8.0
cli     = false

[[parameters]]
name    = "keyhole_slot_width"
meaning = "width of the narrow neck of each keyhole slot the screw shank rides in"
default = 4.0
cli     = false
+++

# Design Brief — pi-mount

A flat baseplate that mounts a Raspberry Pi 4 to a wall. Four standoff bosses on
the front locate and lift the board; two keyhole slots on the back drop over a
pair of wall screws.

## 1. Context & assembly

One printed part. The Pi sits on four bosses arranged in a
`board_hole_spacing_x` x `board_hole_spacing_y` rectangle (58 x 49 mm for a Pi 4),
each boss `boss_height` tall with a `boss_pilot_diameter` pilot hole for an M2.5
self-tapping screw. The plate footprint is the board footprint inflated by
`plate_margin` on each side. Two vertical keyhole slots run up the plate so it
hangs on two wall screws set to the same vertical spacing.

## 2. Tolerances & fits

- **Self-tapping boss pilots.** `boss_pilot_diameter` 2.2 mm is sized for an
  M2.5 screw to cut its own thread in PLA/PETG. It is intentionally not on the
  CLI; change it in the constant if using a different screw.
- **Keyhole fit.** `keyhole_diameter` 8 mm clears a typical screw head;
  `keyhole_slot_width` 4 mm rides the shank. The screw head must pass the round
  entry, then the plate slides down so the shank sits in the narrow neck.

## 3. Print constraints

- **Orientation.** Print plate-back-down (back face on the plate, bosses up). The
  boss pilots and keyhole slots then print as clean vertical holes/channels.
- **Bridging.** The keyhole slots are through-cuts, no bridging. The bosses are
  solid except the pilot.
- `plate_thickness` 3 mm keeps the keyhole region stiff; do not thin it below
  the keyhole geometry or the screw head pocket will break through.

## 4. Named size presets

- **Raspberry Pi 4 / 3B+ / 2B:** hole pattern 58 x 49 mm, board 85 x 56 mm —
  the defaults here.
- **Raspberry Pi Zero:** hole pattern 58 x 23 mm — change
  `board_hole_spacing_y` to 23 and re-check the plate footprint.

## 5. Verification approach

No automated tests. Verify by:

- **Bounding-box sanity check:** plate footprint is
  `85 + 2*plate_margin` x `56 + 2*plate_margin` ~= 97 x 68 mm at defaults; overall
  height is `plate_thickness + boss_height`.
- **Hole-pattern check:** confirm the four boss centers form a 58 x 49 mm
  rectangle, centered on the plate.
- **Physical check:** screw a Pi onto the bosses and hang the plate on two test
  screws.

## 6. Reference sketches

None attached. A front view dimensioning the 58 x 49 mm boss rectangle and the
two keyhole positions would be the most useful reference.

## 7. Out of scope / non-goals

- No enclosure walls, lid, or port cutouts — this is an open baseplate only.
- No cooling, fan mount, or HAT support.
- No VESA or DIN-rail mounting; wall keyholes only.

## 8. Open questions

- Should the keyhole vertical spacing be its own parameter rather than derived
  from the plate height? Deferred to keep the parameter set small.
- Add cable-tie slots along one edge for strain relief? Out of scope for v1.
