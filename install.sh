#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_NAME="$(basename "$SCRIPT_DIR")"

echo "=== ${REPO_NAME} installer ==="

# 1. Install skill
SKILLS_DIR="${HOME}/.claude/skills"
mkdir -p "${SKILLS_DIR}"
ln -sfn "${SCRIPT_DIR}/skills/${REPO_NAME}" "${SKILLS_DIR}/${REPO_NAME}"
echo "  Skill: ${SKILLS_DIR}/${REPO_NAME}"

# 2. Install commands
CMD_DIR="${HOME}/.claude/commands"
mkdir -p "${CMD_DIR}"
for cmd in "${SCRIPT_DIR}"/commands/gt-*.md; do
    [ -f "$cmd" ] || continue
    name="$(basename "$cmd")"
    ln -sf "$cmd" "${CMD_DIR}/${name}"
    echo "  Command: ${name}"
done

echo "Done."
