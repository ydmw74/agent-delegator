#!/usr/bin/env python3
"""
Agent Delegator — OpenAI-compatible API Caller
===============================================
Calls any OpenAI-compatible API endpoint (OpenAI, Gemini, Groq, Mistral,
Ollama, etc.) and returns the model's response to stdout.

Usage:
  python call_openai.py \\
    --prompt "Formatiere diesen Text als Markdown-Tabelle: ..." \\
    --agent-id gpt-4o-mini \\
    --config /path/to/agents.json

  python call_openai.py \\
    --prompt "..." \\
    --api-base https://api.openai.com/v1 \\
    --model gpt-4o-mini \\
    --api-key-env OPENAI_API_KEY

Output:
  Writes model response to stdout (or --output-file if specified).
  Writes metadata JSON to stderr if --verbose.
  Exit code 0 = success, 1 = error.
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error


def load_dotenv(script_dir: str) -> None:
    """Lade .env aus dem Plugin-Root (Elternverzeichnis von scripts/).
    Setzt nur Variablen, die noch nicht in der Umgebung gesetzt sind.
    Unterstützt: KEY=VALUE, KEY="VALUE", KEY='VALUE', Kommentare (#), Leerzeilen.
    """
    plugin_root = os.path.dirname(script_dir)
    env_path = os.path.join(plugin_root, ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def load_agent_config(config_path: str, agent_id: str) -> dict:
    """Load agent configuration from agents.json."""
    try:
        with open(config_path) as f:
            config = json.load(f)
        agents = {a["id"]: a for a in config.get("agents", [])}
        if agent_id not in agents:
            raise ValueError(f"Agent '{agent_id}' not found in config. Available: {list(agents)}")
        agent = agents[agent_id]
        if not agent.get("enabled", False):
            raise ValueError(f"Agent '{agent_id}' is disabled. Enable it in agents.json.")
        return agent
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: {config_path}")


def call_api(
    api_base: str,
    api_key: str,
    model: str,
    prompt: str,
    system_prompt: str,
    max_tokens: int,
    timeout: int,
    verbose: bool,
) -> str:
    """Call the OpenAI-compatible chat completions endpoint."""
    url = f"{api_base.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.3,  # Lower temperature for more deterministic delegation results
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise RuntimeError(f"API error {e.code}: {error_body}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Connection error: {e.reason}")

    elapsed = time.time() - start
    result = body["choices"][0]["message"]["content"]
    usage = body.get("usage", {})

    if verbose:
        meta = {
            "model": model,
            "elapsed_seconds": round(elapsed, 2),
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
        }
        print(json.dumps(meta), file=sys.stderr)

    return result


def main():
    # .env aus Plugin-Root laden (vor allem anderen)
    load_dotenv(os.path.dirname(os.path.abspath(__file__)))

    parser = argparse.ArgumentParser(
        description="Call an OpenAI-compatible API for task delegation."
    )
    # Config-based mode
    parser.add_argument("--agent-id", help="Agent ID from agents.json")
    parser.add_argument(
        "--config",
        default="${CLAUDE_PLUGIN_ROOT}/config/agents.json",
        help="Path to agents.json config file",
    )
    # Direct mode (overrides config)
    parser.add_argument("--api-base", help="API base URL")
    parser.add_argument("--model", help="Model name")
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY", help="Env var with API key")
    parser.add_argument("--max-tokens", type=int, default=4096)

    # Task input
    parser.add_argument("--prompt", required=True, help="Task prompt to send to the model")
    parser.add_argument(
        "--system",
        default=(
            "Du bist ein präziser Assistent. Erledige die gegebene Aufgabe genau und effizient. "
            "Antworte nur mit dem Ergebnis, ohne Erklärungen oder Kommentare, außer wenn explizit gefordert."
        ),
        help="System prompt",
    )
    parser.add_argument("--output-file", help="Write output to file instead of stdout")
    parser.add_argument("--timeout", type=int, default=60, help="Request timeout in seconds")
    parser.add_argument("--verbose", action="store_true", help="Write metadata to stderr")
    parser.add_argument(
        "--task-context",
        default="",
        help="Optional context about the task type (e.g. 'IT project management')",
    )

    args = parser.parse_args()

    # Resolve config path (expand ${CLAUDE_PLUGIN_ROOT})
    config_path = args.config
    if "${CLAUDE_PLUGIN_ROOT}" in config_path:
        plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = config_path.replace("${CLAUDE_PLUGIN_ROOT}", plugin_root)

    # Determine API settings
    if args.agent_id:
        try:
            agent = load_agent_config(config_path, args.agent_id)
        except (FileNotFoundError, ValueError) as e:
            print(f"Config error: {e}", file=sys.stderr)
            sys.exit(1)
        api_base = agent["api_base"]
        model = agent["model"]
        api_key_env = agent["api_key_env"]
        max_tokens = agent.get("max_tokens", args.max_tokens)
    else:
        # Direct mode
        if not args.api_base or not args.model:
            print("Error: either --agent-id or (--api-base + --model) required", file=sys.stderr)
            sys.exit(1)
        api_base = args.api_base
        model = args.model
        api_key_env = args.api_key_env
        max_tokens = args.max_tokens

    # Get API key
    api_key = os.environ.get(api_key_env, "")
    if not api_key:
        # Ollama doesn't require a real key but needs something
        if "localhost" in api_base or "127.0.0.1" in api_base:
            api_key = "ollama"
        else:
            print(
                f"Error: Environment variable '{api_key_env}' is not set.\n"
                f"Set it with: export {api_key_env}=<your-api-key>",
                file=sys.stderr,
            )
            sys.exit(1)

    # Build full prompt
    full_prompt = args.prompt
    if args.task_context:
        full_prompt = f"[Kontext: {args.task_context}]\n\n{full_prompt}"

    # Call the API
    try:
        result = call_api(
            api_base=api_base,
            api_key=api_key,
            model=model,
            prompt=full_prompt,
            system_prompt=args.system,
            max_tokens=max_tokens,
            timeout=args.timeout,
            verbose=args.verbose,
        )
    except RuntimeError as e:
        print(f"API call failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Output result
    if args.output_file:
        with open(args.output_file, "w", encoding="utf-8") as f:
            f.write(result)
        if args.verbose:
            print(f"Output written to: {args.output_file}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()
