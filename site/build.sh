#!/usr/bin/env bash
# Assemble the static demo site into site/dist (Vercel runs this, see vercel.json).
#   /            site/index.html
#   /dashboard/  Fly Brain Live (fly_brain/dashboard)
#   /ride/       the fly learns to ride, attempt by attempt (fly_brain/results/attempts_page: index.html + data/)
#   /ride/3d     16-rider 3D replay of the best decoder, and the other ride_*.html pages
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=site/dist
rm -rf "$OUT"
mkdir -p "$OUT/dashboard/data" "$OUT/ride"

cp site/index.html "$OUT/"

cp fly_brain/dashboard/index.html "$OUT/dashboard/"
cp fly_brain/dashboard/data/*.json fly_brain/dashboard/data/*.png fly_brain/dashboard/data/*.js "$OUT/dashboard/data/"

R=fly_brain/results
cp -r fly_brain/results/attempts_page/. "$OUT/ride/"   # attempts page (index.html + data/), export/export_attempts.py
cp $R/ride_3d.html          "$OUT/ride/3d.html"      # brain steers: best learned decoder, 16 riders, chase cam
cp $R/ride_view.html        "$OUT/ride/charts.html"
cp $R/ride_oracle_3d.html   "$OUT/ride/oracle.html"  # PD rider, no brain
cp $R/ride_oracle_view.html "$OUT/ride/oracle-charts.html"
cp $R/ride_pilot_3d.html    "$OUT/ride/open-loop.html"  # brain in the loop, no steering
cp $R/ride_pilot_view.html  "$OUT/ride/open-loop-charts.html"

du -sh "$OUT"
