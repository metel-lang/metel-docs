#!/usr/bin/env bash
# Wait until metel-core's rolling `develop-latest` binary includes everything this job needs, or
# fail saying exactly what is missing (metel-core#1512).
#
# Why: `check-examples` runs the documentation's examples against the binary core publishes after
# every push to `develop` (delete and recreate; the release's target is the commit it was built
# from). Right after a core merge the job can start before that rebuild finishes, so a docs PR for a
# feature that IS merged failed until someone re-ran it; and a docs PR for a feature that is NOT yet
# merged failed with an example error that did not say why.
#
# What it requires of the binary:
#   - every `Depends-on: metel-lang/metel-core#N` (or `Depends-on: #N`) line in $PR_BODY: that PR
#     must be merged, and the binary must be built from its merge commit or a descendant;
#   - with no such line, the binary must include core `develop` as it is now.
# It polls, up to $WAIT_SECONDS, and fails naming the dependency or the two commits.
#
# Environment: PR_BODY (may be empty), CORE_REPO (default metel-lang/metel-core),
#   WAIT_SECONDS (default 1800), POLL_SECONDS (default 30), GITHUB_OUTPUT (optional).
# Output: the binary's commit, as `core_sha=<sha>` in $GITHUB_OUTPUT and on stdout.
# Needs `gh` authenticated for a public read.

set -euo pipefail

core="${CORE_REPO:-metel-lang/metel-core}"
wait_seconds="${WAIT_SECONDS:-1800}"
poll_seconds="${POLL_SECONDS:-30}"
body="${PR_BODY:-}"

# --- what the binary must include ---------------------------------------------------------------
required=()
labels=()
while IFS= read -r num; do
    [[ -n "$num" ]] || continue
    state="$(gh pr view "$num" --repo "$core" --json state,mergeCommit -q '.state + " " + (.mergeCommit.oid // "")')"
    if [[ "${state%% *}" != "MERGED" ]]; then
        echo "::error::This pull request depends on $core#$num, which is ${state%% *} (not merged). The examples need a $core binary that includes it. Merge it, then re-run this job." >&2
        exit 1
    fi
    required+=("${state##* }")
    labels+=("$core#$num")
done < <(printf '%s\n' "$body" | grep -ioE 'depends-on:[[:space:]]*(metel-lang/metel-core)?#[0-9]+' | grep -oE '[0-9]+$' || true)

if [[ ${#required[@]} -eq 0 ]]; then
    head="$(gh api "repos/$core/commits/develop" -q .sha)"
    required+=("$head")
    labels+=("$core develop@${head:0:8}")
fi

# --- wait for a binary built from those commits or later ----------------------------------------
deadline=$((SECONDS + wait_seconds))
target=""
while true; do
    # the release is deleted and recreated on every core push: a moment with none is not an error
    target="$(gh release view develop-latest --repo "$core" --json targetCommitish -q .targetCommitish 2>/dev/null || true)"
    ready=1
    if [[ -z "$target" ]]; then
        ready=0
    else
        for sha in "${required[@]}"; do
            # `ahead` or `identical`: the binary's commit is the required one or a descendant of it
            status="$(gh api "repos/$core/compare/$sha...$target" -q .status 2>/dev/null || echo error)"
            [[ "$status" == "identical" || "$status" == "ahead" ]] || ready=0
        done
    fi
    [[ $ready -eq 1 ]] && break
    if (( SECONDS >= deadline )); then
        have="missing"
        [[ -z "$target" ]] || have="built from ${target:0:8}"
        shorts=""
        for sha in "${required[@]}"; do shorts+="${sha:0:8} "; done
        echo "::error::Timed out after ${wait_seconds}s: the $core develop-latest binary is $have, but this job needs one that includes ${labels[*]} (commit ${shorts% }). Check that core's 'publish rolling develop binary' job succeeded on develop, then re-run." >&2
        exit 1
    fi
    echo "waiting for a $core binary that includes ${labels[*]} (current: ${target:0:8}${target:-none})..."
    sleep "$poll_seconds"
done

echo "core_sha=$target"
[[ -z "${GITHUB_OUTPUT:-}" ]] || echo "core_sha=$target" >> "$GITHUB_OUTPUT"
