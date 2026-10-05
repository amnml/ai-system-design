# Customer support agent demo

Minimal implementation of [diagram.png](diagram.png) using Google ADK.
One Gemini agent decides which of five Python tools to call. All business data
is fake. Every session acts as customer `C001` (Alex).

## Run

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```sh
cd customer-support-agent
uv sync
cp support_agent/.env.example support_agent/.env
# Set GOOGLE_API_KEY in support_agent/.env using a Google AI Studio key.
uv run adk web --host 127.0.0.1 --no_use_local_storage
```

Open http://127.0.0.1:8000 and select `support_agent`.
For terminal chat instead: `uv run adk run support_agent`.
Gemini calls require an API key and may incur usage charges.

Try these prompts in the same session:

- “Where is my order ORD-1001?” — shipped, with demo tracking.
- “What about ORD-1002?” — processing; conversation history handles follow-ups.
- “What is your return policy?” — local article `KB-RETURNS`.
- “Please refund ORD-1001.” — local ticket pending human review; no money moves.
- “What is the status of TKT-0001?” — retrieves the session's ticket.
- “Show ORD-2001.” — hidden because it belongs to another demo customer.

## Diagram mapping and demo tradeoffs

| Diagram block | Demo implementation |
| --- | --- |
| Customer → chat UI → API → response | ADK's built-in local web UI and server |
| Agent orchestrator + LLM | `support_agent/agent.py`: one ADK `Agent` using Gemini |
| Tool calls | Five functions in `support_agent/tools.py` |
| RAG orchestrator | Keyword retrieval over three local policy articles; no embeddings/vector database |
| Memory | ADK session conversation history; tickets stored through `ToolContext.state` |
| Human in the loop | `human_review` tickets with `pending_human_review` status |
| Auth, gateway, rate limits, scale, monitoring | Production concerns omitted from this local demo |

The order example uses `get_order_details`, which includes status and tracking,
rather than adding a sixth `get_order_status` tool.

Human review is a simulated handoff record, not an approval workflow or a live
support integration. No tool can issue refunds, move money, or cancel orders.
Ticket category selection relies on agent instructions. Tickets are session-local;
IDs can repeat across sessions. The web command uses in-memory storage, so restarting
clears sessions and tickets. There is no cross-session memory or external database.
Demo identity is fixed, not authenticated. Keep the server on localhost.
Production traffic/availability/latency targets in the diagram are not implemented.

## Verify without an API key

```sh
uv run python -m unittest discover -s tests -v
```

Tests cover retrieval, order ownership, ticket lifecycle, duplicate requests,
session isolation, pending human review, and ADK tool schema generation.
They do not test Gemini's live intent routing; use the prompts above for that.

References: [ADK Python quickstart](https://adk.dev/get-started/python/),
[function tools](https://adk.dev/tools-custom/function-tools/),
[session state](https://adk.dev/sessions/state/).
