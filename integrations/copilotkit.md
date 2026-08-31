# ViBo Memory + CopilotKit

Persistent, encrypted memory for your CopilotKit agents: save facts from your backend, retrieve semantically relevant context before every agent call — instead of re-sending the whole history.

**Measured:** 50–150× fewer context tokens, up to 99.9% on large memory stores.

## How it works

- ViBo stores facts as a graph: `label -> content`, with sources, dates and L1/L2/L3 encryption (secrets never reach the LLM).
- Your CopilotKit runtime gets two tools: `vibo_add` (save a fact) and `vibo_find` (retrieve the relevant slice).
- Pattern: before the agent call -> `vibo_find(user_query)` -> inject the slice into context. After the call -> `vibo_add(label, outcome)` -> the next session starts with memory, not from zero.

## Setup

### 1. Start the ViBo MCP server

```bash
npx @vibo-dev/vibo-mcp
```

(Alternative: Python API — see the [ViBo-memory](https://github.com/vnbochkarev-netizen/ViBo-memory) repo.)

### 2. Register the MCP tools in your CopilotKit backend

CopilotKit loads MCP servers as regular tools:

```ts
// vibo_add(label, content, [level])  -> saves a fact (L1 public / L2 private / L3 secret)
// vibo_find(query)                   -> returns the relevant slice (a few hundred tokens)
```

### 3. Use the pattern

Before generation — pull memory:

```ts
const memory = await viboFind(userQuery);
context = [...systemPrompt, ...memory.fragments];
```

After the turn — persist what matters:

```ts
await viboAdd("user-preferences", "Client is on the Pro plan, prefers email summaries");
```

## What you get

- Facts survive session restarts and context compaction.
- Per-agent scopes: each CopilotKit agent/user gets isolated memory (multi-tenant safe).
- Secrets encrypted (L1/L2/L3); nothing sensitive ever reaches the LLM prompt.
- Token savings: 50–150× on context (measured; up to 99.9% on large stores).

## Other integrations

- [n8n workflow](vibo_n8n_workflow.json) · [Dify OpenAPI](vibo_openapi_dify.json) · [headroom](headroom/)
