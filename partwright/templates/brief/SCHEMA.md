# `DESIGN_BRIEF.md` frontmatter schema

This document specifies the structured frontmatter of a `DESIGN_BRIEF.md` file.
It is the single documented contract shared by three consumers: the
`DESIGN_BRIEF.md` template, the design-brief generator (`partwright brief`), and
the new-project scaffolder (`partwright new`). All three are built against this
schema, and this file is the authoritative source for the contract.

## File shape

A `DESIGN_BRIEF.md` is a **TOML frontmatter block** followed by a **Markdown
body**:

- The frontmatter is fenced with `+++` on its own line, before and after the
  TOML.
- The frontmatter is the machine-readable contract the scaffolder consumes. It
  is parsed with Python's standard-library `tomllib`, so it adds no dependency.
- The Markdown body below the closing `+++` is prose the build agent reads. Its
  eight sections are described at the end of this document; they are not part of
  the machine-readable contract.

```
+++
# ... TOML frontmatter ...
+++

# Markdown body
...
```

## Example frontmatter

```toml
+++
project_name = "phone-centipede"          # repo / directory name, identifier-safe
summary      = "A sectioned, dovetail-mating desk phone holder."
units        = "mm"                       # mm | inches — default unit for lengths
components   = ["segment", "nameplate"]   # artifacts the part can build; optional

[coordinate_system]
x = "segment length, along the desk's front edge"
y = "depth, away from the user"
z = "vertical, up off the desk"

[[parameters]]                            # one [[parameters]] block per knob
name    = "segment_length"
meaning = "slab length along X"
default = 101.6                           # in `units` unless `unit` overrides
cli     = false                           # expose as a CLI flag?

[[parameters]]
name    = "slot_angle"
meaning = "slot tilt off vertical, toward +Y"
default = 10.0
unit    = "deg"                           # per-parameter override; omit for lengths
cli     = true
+++
```

## Fields

### Top-level keys

| Key | Required | Type | Default | Meaning |
| --- | --- | --- | --- | --- |
| `project_name` | **required** | string | — | The new repo's directory name and the `generate.py` default STL output name. Should be identifier-safe. |
| `summary` | optional | string | — | One-line description placed in the generated `CLAUDE.md` ("What this is") and `README.md`. |
| `units` | optional | string | `"mm"` | The unit for every length parameter and the unit suffix on generated constants. One of `mm` or `inches`. |
| `components` | optional | array of strings | — | The artifacts the part can build. |

### `[coordinate_system]` table

Optional. A table with three string keys — `x`, `y`, `z` — each giving the
physical meaning of that axis. The per-axis lines are reproduced in the
generated `generate.py` module docstring and `CLAUDE.md`.

| Key | Required | Type | Meaning |
| --- | --- | --- | --- |
| `x` | optional | string | Physical meaning of the +X axis. |
| `y` | optional | string | Physical meaning of the +Y axis. |
| `z` | optional | string | Physical meaning of the +Z axis. |

### `[[parameters]]` array of tables

**Required — one or more.** Each `[[parameters]]` block describes one design
knob. Each becomes a named constant in the generated `generate.py`, and — when
`cli = true` — also an `argparse` flag.

| Key | Required | Type | Meaning |
| --- | --- | --- | --- |
| `name` | **required** | string | The parameter's snake_case identifier. Drives the derived constant name and CLI flag (see below). |
| `meaning` | **required** | string | Short description. Becomes the constant's comment and, for CLI parameters, the flag's help text. Deeper rationale belongs in the Markdown body, not here. |
| `default` | **required** | number | The default value. Interpreted in `units` for lengths, unless `unit` overrides it. |
| `cli` | **required** | boolean | Whether to expose this parameter as a CLI flag. |
| `unit` | optional | string | Per-parameter unit override (e.g. `"deg"`). Omit for plain lengths, which use the top-level `units`. |

## Constant and flag derivation rule

The scaffolder derives the generated constant name and CLI flag from a
parameter's `name` and `unit`:

- **Constant name:** `name` uppercased, with the unit appended as a suffix.
  The unit is `unit` if present, otherwise the top-level `units`.
  Example: `slot_angle` + `unit = "deg"` -> constant `SLOT_ANGLE_DEG`.
  Example: `segment_length` with top-level `units = "mm"` -> constant
  `SEGMENT_LENGTH_MM`.
- **CLI flag:** `name` with underscores replaced by hyphens and a `--` prefix.
  Example: `slot_angle` -> flag `--slot-angle`. The flag is generated only when
  `cli = true`.
- **Comment / help text:** `meaning` becomes the constant's inline comment and,
  for CLI parameters, the `argparse` flag's help text.

## `components` behavior

- If `components` is **omitted**, or contains a **single entry**, the part is a
  one-artifact part and no `--component` flag is generated.
- If `components` contains **more than one entry**, the scaffolder adds a
  `--component` choice flag whose choices are the listed component names.

## Malformed-brief behavior

A brief is **rejected** — the scaffolder never guesses — when either:

- its TOML **fails to parse** (`tomllib` raises), or
- a **required field is missing** (`project_name`, the `[[parameters]]` array,
  or any required key within a `[[parameters]]` block: `name`, `meaning`,
  `default`, `cli`).

In either case the scaffolder exits with a **clear error that names the
problem**.

## Markdown body — the eight sections

Below the closing `+++`, the Markdown body has eight sections (prose for the
build agent; not part of the machine-readable contract):

1. Context & assembly
2. Tolerances & fits
3. Print constraints
4. Named size presets
5. Verification approach
6. Reference sketches
7. Out of scope / non-goals
8. Open questions

Deeper per-parameter rationale lives in this prose — for example under
"Context & assembly" or "Tolerances & fits" — rather than in the one-line
`meaning` field of a `[[parameters]]` block.
