#!/usr/bin/env bash
# Manage per-agent feature worktrees for Linkyard.
#
# Layout:
#   /path/to/linkyard/                    ← main worktree (architect)
#   /path/to/linkyard-worktrees/
#     backend-auth/                       ← backend agent, feature "auth"
#     frontend-search-ui/                 ← frontend agent, feature "search-ui"
#     ...
#
# Branches are named <agent>/<feature-slug>, e.g. backend/auth, frontend/search-ui.

set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
WT_ROOT="$(dirname "$ROOT")/linkyard-worktrees"

AGENTS=(backend frontend extension devops security qa)

usage() {
  cat <<EOF
Usage:
  $(basename "$0") new <agent> <feature>   Create a new feature worktree + branch
  $(basename "$0") list                    List current worktrees
  $(basename "$0") remove <name>           Remove a worktree (must be clean)
  $(basename "$0") prune                   Prune stale worktree refs

Examples:
  $(basename "$0") new backend auth
    → creates \$WT_ROOT/backend-auth on branch backend/auth
  $(basename "$0") new frontend search-ui
    → creates \$WT_ROOT/frontend-search-ui on branch frontend/search-ui

Valid agents: ${AGENTS[*]}
Worktree root: $WT_ROOT
EOF
}

valid_agent() {
  local agent=$1
  for a in "${AGENTS[@]}"; do
    [[ "$a" == "$agent" ]] && return 0
  done
  return 1
}

slugify() {
  echo "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//'
}

cmd_new() {
  local agent=${1:-}
  local feature=${2:-}
  if [[ -z "$agent" || -z "$feature" ]]; then
    echo "error: agent and feature required" >&2
    usage
    exit 1
  fi
  if ! valid_agent "$agent"; then
    echo "error: unknown agent '$agent'. Valid: ${AGENTS[*]}" >&2
    exit 1
  fi

  local slug
  slug="$(slugify "$feature")"
  if [[ -z "$slug" ]]; then
    echo "error: feature name produced an empty slug" >&2
    exit 1
  fi

  local branch="$agent/$slug"
  local path="$WT_ROOT/$agent-$slug"

  mkdir -p "$WT_ROOT"
  if [[ -e "$path" ]]; then
    echo "error: path already exists: $path" >&2
    exit 1
  fi

  local base="main"
  if ! git show-ref --verify --quiet "refs/heads/$base"; then
    echo "error: base branch '$base' does not exist yet. Make the initial commit first." >&2
    exit 1
  fi

  git worktree add -b "$branch" "$path" "$base"

  cat <<EOF

Worktree created
  path:   $path
  branch: $branch
  agent:  $agent

Next steps:
  cd "$path"
  claude   # start a Claude Code session in this worktree

  First prompt (paste verbatim):
    You are the $agent agent for Linkyard. Read .claude/agents/$agent.md and
    act strictly as that role. Do not edit files outside your scope. Feature: $feature.
    Escalate cross-domain questions back to me — I will route them to the architect
    in the main worktree.

EOF
}

cmd_list() {
  git worktree list
}

cmd_remove() {
  local name=${1:-}
  if [[ -z "$name" ]]; then
    echo "error: worktree name required (e.g. backend-auth)" >&2
    exit 1
  fi
  local path="$WT_ROOT/$name"
  if [[ ! -d "$path" ]]; then
    echo "error: no worktree at $path" >&2
    exit 1
  fi
  git worktree remove "$path"
  echo "removed $path"
  echo "note: the branch still exists. Delete it manually if desired: git branch -d <branch>"
}

cmd_prune() {
  git worktree prune -v
}

case "${1:-}" in
  new)    shift; cmd_new "$@" ;;
  list)   shift; cmd_list "$@" ;;
  remove) shift; cmd_remove "$@" ;;
  prune)  shift; cmd_prune "$@" ;;
  -h|--help|help|"") usage ;;
  *) echo "unknown command: $1" >&2; usage; exit 1 ;;
esac
