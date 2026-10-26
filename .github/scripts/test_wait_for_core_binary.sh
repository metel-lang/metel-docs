#!/usr/bin/env bash
# Self-test for wait-for-core-binary.sh (metel-core#1512) with a stubbed `gh`: no network.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
script="$here/wait-for-core-binary.sh"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
mkdir "$tmp/bin"

# A `gh` that answers from files in $FIXTURE: develop (head sha), release (target sha, may be absent
# or change per poll via release.1, release.2, ...), pr-N (state and merge commit), and
# compare-<base>-<head> (status).
cat > "$tmp/bin/gh" <<'STUB'
#!/usr/bin/env bash
set -euo pipefail
args="$*"
case "$args" in
    "pr view "*) n="$3"; cat "$FIXTURE/pr-$n" 2>/dev/null || { echo "no such pr" >&2; exit 1; } ;;
    "api repos/"*"/commits/develop"*) cat "$FIXTURE/develop" ;;
    "release view develop-latest"*)
        count_file="$FIXTURE/polls"; n=$(( $(cat "$count_file" 2>/dev/null || echo 0) + 1 )); echo "$n" > "$count_file"
        if [[ -f "$FIXTURE/release.$n" ]]; then cat "$FIXTURE/release.$n"
        elif [[ -f "$FIXTURE/release" ]]; then cat "$FIXTURE/release"
        else exit 1; fi ;;
    "api repos/"*"/compare/"*)
        range="${2##*/compare/}"; base="${range%%...*}"; head="${range##*...}"
        cat "$FIXTURE/compare-$base-$head" 2>/dev/null || echo "behind" ;;
    *) echo "stub gh: unexpected: $args" >&2; exit 99 ;;
esac
STUB
chmod +x "$tmp/bin/gh"

fail() { echo "FAIL: $*" >&2; exit 1; }
new_case() { FIXTURE="$tmp/case-$1"; rm -rf "$FIXTURE"; mkdir -p "$FIXTURE"; export FIXTURE; }
run() { PATH="$tmp/bin:$PATH" POLL_SECONDS=0 WAIT_SECONDS="${WAIT:-3}" PR_BODY="${BODY:-}" GITHUB_OUTPUT="$FIXTURE/out" "$script" 2>"$FIXTURE/err" >"$FIXTURE/stdout"; }

A=aaaaaaaa11111111111111111111111111111111
B=bbbbbbbb22222222222222222222222222222222

# 1. no dependency: the binary must include develop's head; equal commit passes
new_case 1; echo "$A" > "$FIXTURE/develop"; echo "$A" > "$FIXTURE/release"; echo identical > "$FIXTURE/compare-$A-$A"
run || fail "case 1: should pass"
grep -q "core_sha=$A" "$FIXTURE/out" || fail "case 1: wrong output: $(cat "$FIXTURE/out")"

# 2. a binary ahead of the required commit passes
new_case 2; echo "$A" > "$FIXTURE/develop"; echo "$B" > "$FIXTURE/release"; echo ahead > "$FIXTURE/compare-$A-$B"
run || fail "case 2: should pass"

# 3. the binary is behind: waits, then the rebuild lands and it passes
new_case 3; echo "$B" > "$FIXTURE/develop"; echo "$A" > "$FIXTURE/release.1"; echo "$A" > "$FIXTURE/release.2"; echo "$B" > "$FIXTURE/release"
echo identical > "$FIXTURE/compare-$B-$B"; WAIT=30 run || fail "case 3: should pass after the rebuild"
grep -q "waiting for" "$FIXTURE/stdout" || fail "case 3: should have waited"

# 4. never catches up: times out naming both commits
new_case 4; echo "$B" > "$FIXTURE/develop"; echo "$A" > "$FIXTURE/release"; WAIT=1 
if WAIT=1 run; then fail "case 4: should time out"; fi
grep -q "built from aaaaaaaa" "$FIXTURE/err" && grep -q "bbbbbbbb" "$FIXTURE/err" || fail "case 4: message should name both: $(cat "$FIXTURE/err")"

# 5. the release is momentarily absent (delete and recreate), then appears
new_case 5; echo "$A" > "$FIXTURE/develop"; echo "$A" > "$FIXTURE/release"; echo identical > "$FIXTURE/compare-$A-$A"
echo "$A" > "$FIXTURE/release"; rm "$FIXTURE/release"; echo "$A" > "$FIXTURE/release.3"
echo "$A" > "$FIXTURE/release.4"; WAIT=30 run || fail "case 5: a missing release should be retried"

# 6. Depends-on: a PR that is still open fails at once and names it
new_case 6; echo "OPEN " > "$FIXTURE/pr-1234"; BODY="Documents the thing.

Depends-on: metel-lang/metel-core#1234" 
if BODY="Depends-on: metel-lang/metel-core#1234" run; then fail "case 6: an open dependency should fail"; fi
grep -q "metel-lang/metel-core#1234" "$FIXTURE/err" && grep -q "OPEN" "$FIXTURE/err" || fail "case 6: message: $(cat "$FIXTURE/err")"

# 7. Depends-on: a merged PR requires the binary to include its merge commit
new_case 7; echo "MERGED $A" > "$FIXTURE/pr-77"; echo "$B" > "$FIXTURE/release"; echo ahead > "$FIXTURE/compare-$A-$B"
BODY="Depends-on: #77" run || fail "case 7: should pass"
grep -q "core_sha=$B" "$FIXTURE/out" || fail "case 7: wrong output"

# 8. a merged dependency whose commit the binary lacks times out naming it
new_case 8; echo "MERGED $B" > "$FIXTURE/pr-78"; echo "$A" > "$FIXTURE/release"
if BODY="Depends-on: #78" WAIT=1 run; then fail "case 8: should time out"; fi
grep -q "metel-lang/metel-core#78" "$FIXTURE/err" || fail "case 8: message should name the dependency: $(cat "$FIXTURE/err")"

echo "wait-for-core-binary: all checks passed"
