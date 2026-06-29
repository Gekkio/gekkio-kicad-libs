#!/usr/bin/env bash
# Re-save every symbol and footprint library in this repo with the current
# kicad-cli, forcing a rewrite so files match the installed KiCad version.

set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")"/..

shopt -s nullglob

for sym in Gekkio_*.kicad_sym; do
	echo "sym upgrade: $sym"
	kicad-cli sym upgrade --force "$sym"
done

for pretty in Gekkio_*.pretty; do
	echo "fp upgrade:  $pretty"
	kicad-cli fp upgrade --force "$pretty"
done
