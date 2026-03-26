<p align="center">
  <h1 align="center">spagents</h1>
  <p align="center">
    <strong>Give your AI agents eyes for the modern web.</strong>
  </p>
  <p align="center">
    <a href="#installation">Installation</a> &middot;
    <a href="#quick-start">Quick Start</a> &middot;
    <a href="#mcp-server">MCP Server</a> &middot;
    <a href="#python-sdk">Python SDK</a> &middot;
    <a href="#how-it-works">How It Works</a>
  </p>
</p>

---

**AI agents are blind to Single Page Applications.** Tools like `fetch` and `requests` return empty HTML shells — no articles, no content, no interactive elements. SPAs render everything via JavaScript *after* the page loads.

**spagents** fixes this. It launches a real browser, intelligently waits for SPAs to finish rendering, and returns structured, agent-friendly data — articles, actions, inputs, navigation — ready for your agent to use.

### The problem

```
# What fetch/requests sees on a SPA:
<div id="app"></div>
<script src="bundle.js"></script>
```

### The spagents solution

```bash
$ spagents browse "https://news.kagi.com" --format text

Title: World | Kagi News
Content Ready: True

=== 12 Articles ===
  MIDDLE EAST: Update: Iran rejects US truce plan, sets terms
  TECH ACCOUNTABILITY: US jury holds Meta, YouTube liable in addiction case
  ARCHAEOLOGY: Possible d'Artagnan remains found beneath Maastricht church
  ...

=== 45 Actions ===
  [1] (navigate) Listitem: Technology
  [2] (click)    Button: Expand story (Iran rejects US truce plan...)
  [3] (input)    Input: Search
  ...
```

### Key features

- **Smart content detection** — Knows when a SPA is done rendering (not just `sleep(5)`)
- **Structured extraction** — Returns articles, links, metadata as typed Pydantic models
- **Full interaction** — Click, type, scroll, press keys, navigate — like a real user
- **Action discovery** — Finds every interactive element: buttons, inputs, ARIA roles, custom components
- **Session persistence** — Cookies, localStorage, and auth state preserved across navigations
- **Three interfaces** — Python SDK, CLI, and MCP server for Claude Desktop / AI agents

---

## Installation

```bash
pip install spagents
playwright install chromium
```

### From source

```bash
git clone https://github.com/your-username/spagents.git
cd spagents
uv sync
uv run playwright install chromium
```

## Quick start

### CLI

```bash
# Structured JSON output (default)
spagents browse "https://news.kagi.com"

# Human-readable text
spagents browse "https://news.kagi.com" --format text

# Interactive REPL session
spagents interactive "https://news.kagi.com"
```

### Python SDK

```python
import asyncio
from spagents import BrowserManager

async def main():
    async with BrowserManager() as browser:
        session = await browser.new_session()

        # Browse a SPA — content is fully rendered
        state = await session.navigate("https://news.kagi.com")
        for article in state.content.articles:
            print(f"{article.category}: {article.headline}")

        # Interact with the page
        for action in state.actions:
            if "Technology" in action.description:
                state = await session.click(action.selector)
                break

        # Type into inputs, press keys
        state = await session.type_text("#search", "climate change")
        state = await session.press_key("Enter")

        await session.close()

asyncio.run(main())
```

### MCP Server

Connect spagents to Claude Desktop or any MCP-compatible AI agent:

```bash
spagents mcp
```

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "spagents": {
      "command": "spagents",
      "args": ["mcp"]
    }
  }
}
```

#### Claude Code

Add the MCP server to your project or user settings:

```bash
claude mcp add spagents -- spagents mcp
```

Or add it directly to your `.claude/settings.json`:

```json
{
  "mcpServers": {
    "spagents": {
      "command": "spagents",
      "args": ["mcp"]
    }
  }
}
```

Now Claude can browse any SPA:

> **You:** "What's the top story on Kagi News today?"
>
> **Claude:** *uses `browse` tool* → *reads structured articles* → gives you the answer

#### MCP tools

| Tool | Description |
|---|---|
| `browse` | Navigate to a URL, return rendered content + interactive actions |
| `click` | Click an element by CSS selector |
| `type_text` | Type into an input field |
| `press_key` | Press a keyboard key (Enter, Tab, Escape, etc.) |
| `list_actions` | Discover all interactive elements on the page |
| `navigate` | Go to a new URL within an existing session |
| `scroll` | Scroll up or down, trigger infinite scroll |
| `extract_content` | Re-extract content from the current page |
| `close_session` | Close a browser session and free resources |

## Interactive REPL commands

```
click <n>                  Click action by number
click <selector>           Click by CSS selector
type <n> <text>            Type text into an input by action number
type "<selector>" <text>   Type text into an input by CSS selector
press <key>                Press a key (Enter, Escape, Tab, ArrowDown, etc.)
select <n> <value>         Select dropdown option by action number
scroll [down|up]           Scroll the page
actions                    List all interactive elements
extract                    Re-extract page content
navigate <url>             Navigate to a new URL
json                       Dump current state as JSON
quit                       Exit the session
```

## How it works

spagents wraps [Playwright](https://playwright.dev/python/) and adds three intelligent layers:

### 1. Content ready detection

A multi-signal detector that knows when a SPA has *actually* finished rendering:

| Signal | What it checks |
|---|---|
| **Network quiescence** | No pending XHR/fetch requests for 500ms (ignoring analytics noise) |
| **DOM stabilization** | MutationObserver sees no changes for 300ms after initial render |
| **Content heuristic** | Meaningful text exists, no loading spinners, real links present |

This replaces naive approaches like `sleep(5)` or Playwright's `networkidle` (which breaks on long-polling and WebSocket connections).

### 2. Content extraction

Extracts structured data from the rendered DOM:

- **Articles** with headlines, summaries, sources, highlights, quotes, and sections
- **Links** with surrounding context (which heading or section they're under)
- **Metadata** from OG tags, meta descriptions, and page title

### 3. Action discovery

Finds *every* interactive element on the page through four phases:

1. **Semantic HTML** — `<a>`, `<button>`, `<input>`, `<select>`
2. **ARIA roles** — `role="button"`, `role="tab"`, `role="listitem"`, etc.
3. **Custom components** — `tabindex`, `onclick`, `cursor: pointer`
4. **Disambiguation** — Duplicate labels get context from parent containers

## CLI reference

```
spagents browse <url> [OPTIONS]
  --format, -f    Output format: json (default) or text
  --timeout, -t   Content detection timeout in ms (default: 15000)
  --no-headless   Run browser with visible window

spagents interactive <url> [OPTIONS]
  --timeout, -t   Content detection timeout in ms (default: 15000)
  --no-headless   Run browser with visible window

spagents mcp [OPTIONS]
  --transport     Transport: stdio (default) or sse
  --port, -p      Port for SSE transport (default: 8000)
```

## License

MIT with an amended community contribution requirement for organizations with
more than 100 employees. See [LICENSE.md](LICENSE.md) for details.
