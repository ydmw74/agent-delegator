#!/usr/bin/env bash
# =============================================================================
# Agent Delegator — opencode CLI Wrapper
# =============================================================================
# Delegates a coding task to the opencode CLI and captures the result.
#
# opencode is a terminal-based AI coding assistant. This wrapper supports
# its non-interactive "run" mode.
#
# Usage:
#   ./call_opencode.sh --prompt "Schreibe Unit-Tests für diese Funktion: ..."
#   ./call_opencode.sh --prompt "..." --output-file /tmp/result.txt
#   ./call_opencode.sh --prompt "..." --model claude-haiku-4-5-20251001
#
# Environment variables:
#   OPENCODE_DELEGATE_MODEL   Model to use (default: claude-haiku-4-5-20251001)
#   OPENCODE_DELEGATE_ARGS    Extra args to pass to opencode (optional)
#
# Exit codes:
#   0  Success
#   1  Error (opencode not found, execution failed, etc.)
# =============================================================================

set -euo pipefail

# Defaults
PROMPT=""
OUTPUT_FILE=""
MODEL="${OPENCODE_DELEGATE_MODEL:-claude-haiku-4-5-20251001}"
VERBOSE=false
EXTRA_ARGS="${OPENCODE_DELEGATE_ARGS:-}"
TIMEOUT_SECS=120

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --prompt)       PROMPT="$2";      shift 2 ;;
    --output-file)  OUTPUT_FILE="$2"; shift 2 ;;
    --model)        MODEL="$2";       shift 2 ;;
    --verbose)      VERBOSE=true;     shift   ;;
    --timeout)      TIMEOUT_SECS="$2"; shift 2 ;;
    --help|-h)
      grep '^#' "$0" | sed 's/^# \?//'
      exit 0 ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1 ;;
  esac
done

# Validate input
if [[ -z "$PROMPT" ]]; then
  echo "Error: --prompt is required" >&2
  exit 1
fi

# Check if opencode is available
if ! command -v opencode &> /dev/null; then
  echo "Error: opencode CLI not found." >&2
  echo "Install: npm install -g opencode-ai  (or check https://opencode.ai)" >&2
  echo "" >&2
  echo "Alternatively, configure a different agent in config/agents.json." >&2
  exit 1
fi

[[ "$VERBOSE" == true ]] && echo "[delegate] Running opencode with model: $MODEL" >&2

# Write prompt to a temp file (avoids shell escaping issues with long prompts)
PROMPT_FILE=$(mktemp /tmp/delegate_prompt_XXXXXX.txt)
echo "$PROMPT" > "$PROMPT_FILE"
trap 'rm -f "$PROMPT_FILE"' EXIT

# Run opencode
# The `opencode run` subcommand processes a prompt non-interactively.
# If your version of opencode uses a different interface, adjust accordingly:
#   - Some versions: opencode --print-only "prompt"
#   - Some versions: opencode chat --no-interactive < prompt.txt
#   - Check: opencode --help
RESULT=$(
  timeout "$TIMEOUT_SECS" opencode run \
    --model "$MODEL" \
    --no-interactive \
    $EXTRA_ARGS \
    < "$PROMPT_FILE" 2>/dev/null
) || {
  EXIT_CODE=$?
  if [[ $EXIT_CODE -eq 124 ]]; then
    echo "Error: opencode timed out after ${TIMEOUT_SECS}s" >&2
  else
    echo "Error: opencode exited with code $EXIT_CODE" >&2
    echo "Tip: Check opencode --help for the correct non-interactive syntax for your version." >&2
  fi
  exit 1
}

# Output result
if [[ -n "$OUTPUT_FILE" ]]; then
  echo "$RESULT" > "$OUTPUT_FILE"
  [[ "$VERBOSE" == true ]] && echo "[delegate] Output written to: $OUTPUT_FILE" >&2
else
  echo "$RESULT"
fi
