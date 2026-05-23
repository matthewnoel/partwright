+++
# === DESIGN_BRIEF.md frontmatter =============================================
# This TOML block is the machine-readable contract the scaffolder consumes.
# It MUST conform to templates/brief/SCHEMA.md. Replace every value below with
# the real design; keep the keys. Parsed with the stdlib `tomllib`.

project_name = "my-part"            # REQUIRED. Repo / directory name and the
                                    # generate.py default STL name. Identifier-safe.
summary      = "One-line description of the part."  # optional; goes in CLAUDE.md
                                                    # ("What this is") and README.md
units        = "mm"                 # optional, default "mm". One of: mm | inches.
                                    # Default unit for every length parameter.
components   = ["main"]             # optional. The artifacts generate.py can build.
                                    # Omit, or give one entry, for a single-artifact
                                    # part. More than one entry adds a --component
                                    # choice flag. e.g. ["segment", "nameplate"].

[coordinate_system]                 # optional. Reproduced verbatim in the
                                    # generate.py docstring and CLAUDE.md.
                                    # Give each axis a concrete physical meaning.
x = "physical meaning of the +X axis"
y = "physical meaning of the +Y axis"
z = "physical meaning of the +Z axis"

# --- Parameters --------------------------------------------------------------
# REQUIRED: one or more [[parameters]] blocks. Each becomes a named constant in
# generate.py; when cli = true it also becomes an --argparse flag.
#   Constant name: NAME uppercased + unit suffix  (length_x -> LENGTH_X_MM,
#                  slot_angle + unit="deg" -> SLOT_ANGLE_DEG).
#   CLI flag:      name with underscores -> hyphens  (slot_angle -> --slot-angle).
#   meaning:       becomes the constant's comment and the flag's help text.
# Keep `meaning` to one line; put rationale in the Markdown body below.

[[parameters]]
name    = "overall_length"          # REQUIRED. snake_case identifier.
meaning = "part length along X"     # REQUIRED. One-line description.
default = 100.0                     # REQUIRED. Number; in `units` unless `unit` set.
cli     = true                      # REQUIRED. Expose as a CLI flag?

[[parameters]]
name    = "wall_thickness"
meaning = "thickness of the part's side walls"
default = 2.4
cli     = false

[[parameters]]
name    = "tilt_angle"
meaning = "feature tilt off vertical"
default = 10.0
unit    = "deg"                     # optional per-parameter unit override.
                                    # Omit for plain lengths (they use `units`).
cli     = true
+++

# Design Brief — <part name>

<One short paragraph: what the part is, what it is for, how many printed pieces
it assembles from, and its rough overall size with default parameters.>

## 1. Context & assembly

<What the part is and the problem it solves. Who or what uses it, in what
setting. Whether it is a finished functional part, a prototype, or a jig.>

<What it mates with — other printed parts, a purchased object, or nothing. For
each mating interface: which faces or features touch and how they are held
together (friction, snap-fit, fasteners, dovetail/slide, gravity). If it
assembles from multiple pieces, how many and in what order.>

<The controlling relationship at each interface — the explicit equation tying
one dimension to another (e.g. "lip outer size = cavity inner size −
2 × fit_clearance"). This is also where deeper per-parameter rationale belongs,
not in the one-line `meaning` fields above.>

## 2. Tolerances & fits

<For every mating interface, the fit wanted (press / friction / sliding /
loose) and the per-side clearance value that achieves it on a calibrated FDM
printer. Note which clearance is a CLI flag and why (printer/filament-dependent
values belong on the CLI so they can be tuned between prints).>

<Reference values: ~0.10–0.15 mm/side is a snug press fit; ~0.20–0.30 mm/side
is a sliding/loose fit; zero or negative will not assemble.>

<Any walls or features near the FDM thin-feature limit — relate thickness to a
0.4 mm nozzle (perimeter counts) and note the minimum safe value.>

## 3. Print constraints

<Build-plate orientation for each component — which face sits down as printed,
and why that orientation was chosen.>

<Overhangs steeper than ~45° and any spans that must bridge; whether
orientation eliminates them. Whether the part prints support-free.>

<First-layer / adhesion / warping notes: wide flat first layers, sharp corners
prone to lifting, brim needs.>

<Boolean-robustness notes: any cut or fuse that lands on a part face. The build
agent adds face-overlap tabs / overshoots so OCCT never resolves a coincident
face — flag where this is needed.>

## 4. Named size presets

<If the part is sized to known real-world objects (a specific phone model, a
battery cell, a standard rail), list the presets and their dimensions here.
The scaffolder stays generic; the build agent adds any lookup module. If the
part is fully parametric with no presets, write "None — fully parametric" and
say how it is sized directly.>

## 5. Verification approach

<How a finished STL is checked. The expected bounding box with default
parameters — work out the numbers — is the cheap sanity check. Re-slicing in
Bambu Studio to confirm orientation and support-free printing. Any physical fit
checks (print piece A and B, confirm they assemble). Normally there are no
automated tests.>

## 6. Reference sketches

<List the relevant sketches in `sketches/` and what each shows (top view, front
section, exploded assembly). Note any drawn in precise mode with a real
millimeter scale. If none exist, say so and describe the one sketch that would
most help the build agent.>

## 7. Out of scope / non-goals

<What this part deliberately does NOT do — features explicitly excluded, so the
build agent does not add them. e.g. "no hinge or latch", "no internal
dividers", "not watertight", "no embossed text".>

## 8. Open questions

<Anything left undecided after the interview. Each item: the question, the
current leaning, and what would resolve it. The build agent treats these as
known unknowns rather than guessing.>
