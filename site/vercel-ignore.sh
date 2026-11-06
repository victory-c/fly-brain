#!/usr/bin/env bash
# Vercel's Ignored Build Step (vercel.json "ignoreCommand"): exit 0 skips the build, exit 1 builds.
# A skipped build saves the build but still counts as one of the account's deployments for the day.
# cron pushes logs and results every 30 min; the site only needs rebuilding when something build.sh copies
# has changed since the commit Vercel last deployed. Any doubt (no previous deployment, commit not
# fetchable) builds.
INPUTS=(
  vercel.json site
  fly_brain/dashboard/index.html fly_brain/dashboard/data
  fly_brain/results/attempts_page
  fly_brain/results/ride_3d.html fly_brain/results/ride_view.html
  fly_brain/results/ride_oracle_3d.html fly_brain/results/ride_oracle_view.html
  fly_brain/results/ride_pilot_3d.html fly_brain/results/ride_pilot_view.html
)
PREV=${VERCEL_GIT_PREVIOUS_SHA:-}
[ -n "$PREV" ] || { echo "no previous deployment: build"; exit 1; }
# Vercel's clone is 10 commits deep and a skipped build does not move PREV, so PREV soon falls outside it:
# fetch that one commit by URL (public repo; the clone may have no usable "origin")
REPO_URL="https://github.com/${VERCEL_GIT_REPO_OWNER:-victory-c}/${VERCEL_GIT_REPO_SLUG:-fly-brain}.git"
git cat-file -e "$PREV^{commit}" 2>/dev/null || git fetch -q --depth=1 "$REPO_URL" "$PREV" 2>/dev/null \
  || { echo "cannot reach $PREV: build"; exit 1; }
if git diff --quiet "$PREV" HEAD -- "${INPUTS[@]}"; then
  echo "nothing the site is built from changed since ${PREV:0:7}: skip"
  exit 0
fi
echo "site inputs changed since ${PREV:0:7}: build"
git diff --stat "$PREV" HEAD -- "${INPUTS[@]}" | tail -5
exit 1
