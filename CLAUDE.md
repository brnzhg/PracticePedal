# PracticePedal

3D-printed Bluetooth page-turner pedal: build123d CAD in `pedal_cad/`, ZMK firmware config at the
repo root. See README.md for the design, parts, and assembly.

## CAD

- All dimensions live in `pedal_cad/params.py`; geometry in `parts.py`; SVG drawings in `draw.py`.
- `uv run python -m pedal_cad.build` rebuilds everything, runs the fit checks, and rewrites `out/`
  (STEP, STL, drawings). It exits non-zero if a check fails. Run it after any geometry change and
  commit the regenerated `out/drawings/` with the source. `out/stl/` and `out/step/` are gitignored;
  CI (`.github/workflows/cad.yml`) builds them as an artifact, and attaches them to a release on `v*` tags.
- `uv run python -m pedal_cad.view [exploded | pressed <key> | <part>...]` sends the model to the
  OCP CAD Viewer panel in VS Code (port 3939). Geometry only, no checks, no exports.
- STLs are exported in print orientation (sled, top, riser flipped); STEPs are as used.

## Firmware

- ZMK v0.3 shield in `boards/shields/practice_pedal/`, keymap and settings in `config/`.
- `./scripts/build-firmware.sh` builds in the ZMK container (podman) into `out/firmware/`. The first
  run downloads about 1 GB into `.zmk-workspace/`. CI builds the same on push.
