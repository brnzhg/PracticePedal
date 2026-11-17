#!/usr/bin/env bash
# Build the firmware locally in the official ZMK container (podman or docker).
# Output: out/firmware/practice_pedal.uf2 and settings_reset.uf2
# The west workspace is cached in .zmk-workspace/ (about 1 GB, first run is slow).
set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
engine="$(command -v podman || command -v docker)"
ws="$repo/.zmk-workspace"
mkdir -p "$ws" "$repo/out/firmware"
"$engine" run --rm --security-opt label=disable \
  -v "$repo:/repo:ro" -v "$ws:/ws" -v "$repo/out/firmware:/out" -w /ws \
  docker.io/zmkfirmware/zmk-build-arm:3.5 bash -euc '
    rm -rf config && cp -r /repo/config config
    [ -d .west ] || west init -l config
    west update --narrow --fetch-opt=--depth=1
    west zephyr-export
    for shield in practice_pedal settings_reset; do
      west build -p -s zmk/app -d build/$shield -b nice_nano_v2 -- \
        -DSHIELD=$shield -DZMK_CONFIG=/ws/config -DZMK_EXTRA_MODULES=/repo
      cp build/$shield/zephyr/zmk.uf2 /out/$shield.uf2
    done'
ls -l "$repo/out/firmware"
