"""CLI entry point for spagents."""

from __future__ import annotations

import asyncio
import sys

import typer

from spagents.browser.manager import BrowserManager

app = typer.Typer(
    name="spagents",
    help="SPA-aware browsing for AI agents",
    no_args_is_help=True,
)


def _print_article(i: int, article) -> None:
    """Print a single article in human-readable format."""
    if article.expanded:
        # Rich expanded article display
        if article.category:
            print(f"\n{'─' * 60}")
            print(f"  {article.category}")
        print(f"\n  {article.headline}")
        print(f"{'─' * 60}")

        if article.location:
            print(f"  Location: {article.location}")

        if article.summary:
            print()
            for para in article.summary.split("\n\n"):
                print(f"  {para}")

        if article.images:
            print()
            for img in article.images:
                print(f"  [Image: {img}]")

        if article.sources:
            print(f"\n  Sources ({len(article.sources)} publishers)")
            for src in article.sources:
                time_str = f"  {src.time_ago}" if src.time_ago else ""
                count_str = f" ({src.article_count} articles)" if src.article_count > 1 else ""
                print(f"    - {src.name}{time_str}{count_str}")
                if src.url:
                    print(f"      {src.url}")

        if article.highlights:
            print(f"\n  Highlights")
            for j, hl in enumerate(article.highlights, 1):
                print(f"\n    {j}. {hl.title}")
                print(f"       {hl.text}")

        if article.quotes:
            print()
            for quote in article.quotes:
                print(f'  > "{quote}"')

        if article.perspectives:
            print(f"\n  Perspectives")
            for persp in article.perspectives:
                print(f"\n    {persp.speaker}:")
                print(f"    {persp.text}")

        for section in article.sections:
            print(f"\n  {section.heading}")
            print(f"  {section.text[:500]}")
    else:
        # Collapsed article card
        prefix = f"  {article.category}: " if article.category else "  "
        print(f"\n{i}. {prefix}{article.headline}")
        if article.source:
            print(f"   Source: {article.source}")
        if article.summary:
            print(f"   {article.summary[:200]}")
        if article.url:
            print(f"   {article.url}")


def _print_state_text(state) -> None:
    """Print a PageState in human-readable text format."""
    print(f"Title: {state.title}")
    print(f"URL: {state.url}")
    print(f"Content Ready: {state.content_ready}")
    if state.session_id:
        print(f"Session: {state.session_id}")
    print()
    if state.content.articles:
        print(f"=== {len(state.content.articles)} Articles ===")
        for i, article in enumerate(state.content.articles, 1):
            _print_article(i, article)
    else:
        print("=== Main Text ===")
        print(state.content.main_text[:2000])
    print(f"\n=== {len(state.content.links)} Links ===")
    for link in state.content.links[:20]:
        ctx = f" [{link.context}]" if link.context else ""
        print(f"  {link.text[:80]}{ctx} -> {link.url}")
    if state.actions:
        print(f"\n=== {len(state.actions)} Actions ===")
        for i, action in enumerate(state.actions[:30], 1):
            print(f"  [{i}] ({action.action_type}) {action.description}")
            print(f"      selector: {action.selector}")


def _parse_target_and_arg(arg: str, actions: list) -> tuple:
    """Parse '<number> <value>' or '"<selector>" <value>' from a command argument.

    Returns (selector, value) or (None, None) on failure (with message printed).
    """
    # Try action number first
    parts = arg.split(maxsplit=1)
    if parts[0].isdigit():
        idx = int(parts[0]) - 1
        if not actions or idx < 0 or idx >= len(actions):
            print("Invalid action number. Use 'actions' to see available actions.")
            return None, None
        if len(parts) < 2:
            print("Missing value argument.")
            return None, None
        return actions[idx].selector, parts[1]

    # Try quoted selector: "some selector" value
    if arg.startswith('"'):
        end_quote = arg.find('"', 1)
        if end_quote == -1:
            print('Unterminated quote. Usage: type "<selector>" <text>')
            return None, None
        selector = arg[1:end_quote]
        rest = arg[end_quote + 1:].strip()
        if not rest:
            print("Missing value argument.")
            return None, None
        return selector, rest

    # Fallback: first token is selector, rest is value
    if len(parts) < 2:
        print('Usage: <number> <value> or "<selector>" <value>')
        return None, None
    return parts[0], parts[1]


async def _browse(url: str, timeout: int, headless: bool, text_mode: bool) -> None:
    async with BrowserManager(headless=headless) as manager:
        page = await manager.new_page()
        page._detector.timeout_ms = timeout
        state = await page.goto(url)
        await page.close()

    if text_mode:
        _print_state_text(state)
    else:
        print(state.model_dump_json(indent=2))


async def _interactive(url: str, timeout: int, headless: bool) -> None:
    async with BrowserManager(headless=headless) as manager:
        session = await manager.new_session()
        session.page._detector.timeout_ms = timeout

        print(f"Session {session.id} started. Navigating to {url}...")
        state = await session.navigate(url)
        _print_state_text(state)

        print("\n--- Commands: click <n>, type <n> <text>, press <key>, scroll [down|up], actions, extract, navigate <url>, json, quit ---")

        while True:
            try:
                cmd = input("\nspagents> ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not cmd:
                continue

            parts = cmd.split(maxsplit=1)
            command = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            try:
                if command == "quit" or command == "exit":
                    break

                elif command == "click":
                    if not arg:
                        print("Usage: click <number> or click <selector>")
                        continue
                    # Allow clicking by action number or raw selector
                    if arg.isdigit():
                        idx = int(arg) - 1
                        if not state.actions or idx < 0 or idx >= len(state.actions):
                            print(f"Invalid action number. Use 'actions' to see available actions.")
                            continue
                        selector = state.actions[idx].selector
                        print(f"Clicking: {state.actions[idx].description}")
                    else:
                        selector = arg
                        print(f"Clicking: {selector}")
                    state = await session.click(selector)
                    _print_state_text(state)

                elif command == "type":
                    # type <action_number> <text>
                    # type "<selector>" <text>
                    if not arg:
                        print('Usage: type <number> <text> or type "<selector>" <text>')
                        continue
                    selector, text = _parse_target_and_arg(arg, state.actions)
                    if selector is None:
                        continue
                    print(f"Typing into: {selector}")
                    state = await session.type_text(selector, text)
                    _print_state_text(state)

                elif command == "press":
                    if not arg:
                        print("Usage: press <key> (e.g. Enter, Escape, Tab, ArrowDown)")
                        continue
                    print(f"Pressing: {arg}")
                    state = await session.press_key(arg)
                    _print_state_text(state)

                elif command == "select":
                    if not arg:
                        print('Usage: select <number> <value> or select "<selector>" <value>')
                        continue
                    selector, value = _parse_target_and_arg(arg, state.actions)
                    if selector is None:
                        continue
                    print(f"Selecting: {value}")
                    state = await session.select_option(selector, value)
                    _print_state_text(state)

                elif command == "scroll":
                    direction = arg.lower() if arg else "down"
                    print(f"Scrolling {direction}...")
                    state = await session.scroll(direction)
                    _print_state_text(state)

                elif command == "actions":
                    actions = await session.actions()
                    print(f"\n=== {len(actions)} Actions ===")
                    for i, action in enumerate(actions[:50], 1):
                        print(f"  [{i}] ({action.action_type}) {action.description}")
                        print(f"      selector: {action.selector}")

                elif command == "extract":
                    state = await session.extract()
                    _print_state_text(state)

                elif command == "navigate" or command == "goto":
                    if not arg:
                        print("Usage: navigate <url>")
                        continue
                    print(f"Navigating to {arg}...")
                    state = await session.navigate(arg)
                    _print_state_text(state)

                elif command == "json":
                    print(state.model_dump_json(indent=2))

                else:
                    print(f"Unknown command: {command}")
                    print("Commands: click <n>, type <n> <text>, press <key>, select <n> <value>,")
                    print("         scroll [down|up], actions, extract, navigate <url>, json, quit")

            except Exception as e:
                print(f"Error: {e}")

        await session.close()
        print("Session closed.")


@app.command("browse")
def browse(
    url: str = typer.Argument(help="URL to browse"),
    format: str = typer.Option("json", "--format", "-f", help="Output format: json or text"),
    timeout: int = typer.Option(15000, "--timeout", "-t", help="Timeout in ms for content detection"),
    headless: bool = typer.Option(True, help="Run browser in headless mode"),
) -> None:
    """Navigate to a URL, wait for SPA content to render, and extract structured data."""
    text_mode = format.lower() == "text"
    try:
        asyncio.run(_browse(url, timeout, headless, text_mode))
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command("interactive")
def interactive(
    url: str = typer.Argument(help="URL to start browsing"),
    timeout: int = typer.Option(15000, "--timeout", "-t", help="Timeout in ms for content detection"),
    headless: bool = typer.Option(True, help="Run browser in headless mode"),
) -> None:
    """Start an interactive browsing session with a REPL."""
    try:
        asyncio.run(_interactive(url, timeout, headless))
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command("mcp")
def mcp_server(
    transport: str = typer.Option("stdio", "--transport", help="Transport: stdio or sse"),
    port: int = typer.Option(8000, "--port", "-p", help="Port for SSE transport"),
) -> None:
    """Start the MCP server for AI agent integration."""
    from spagents.mcp.server import mcp

    if transport == "sse":
        mcp.run(transport="sse", port=port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    app()
