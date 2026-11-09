"""
mcp_server.py
=============
Model Context Protocol (MCP) server over the chatbot's calculation tools.

The React chat calls the tools in-process through ``chatbot.agent``; this
module is a second transport over the *same* registry, for external MCP
clients (Claude Desktop, Claude Code). The tool list is generated from
``chatbot.tools.TOOL_DEFINITIONS`` and every call goes through
``chatbot.tools.dispatch_tool``, so the two transports cannot drift: a tool
added to the registry appears here with no edit to this file.

Transport is stdio only::

    pip install -e ".[mcp]"
    python -m suryasiddhanta.mcp_server

The ``mcp`` SDK is an optional extra, imported lazily inside
:func:`build_server`, so importing this module without it does not fail;
building the server does, with a :class:`RuntimeError` naming the extra.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:  # pragma: no cover - typing only
    from mcp.server import Server

#: Name the server reports to clients in its ``initialize`` response.
SERVER_NAME = "suryasiddhanta"

#: Shown to clients that surface server instructions to the model.
SERVER_INSTRUCTIONS = (
    "Calculation tools for the Surya Siddhanta (Burgess 1860 translation), "
    "computed from the text's own formulas, not a modern ephemeris. Dates are "
    "civil dates; clock times are in the zone given by a tool's utc_offset "
    "(IST, 5.5, by default). Longitudes are sidereal. Corpus tools "
    "(search_corpus, get_verse, ...) return citable verse ids; cite those "
    "rather than quoting the text from memory."
)

_MISSING_SDK_MESSAGE = (
    "The MCP server needs the 'mcp' SDK, which is an optional extra. "
    'Install it with: pip install -e ".[mcp]"'
)


def _server_version() -> str:
    """
    The installed ``suryasiddhanta`` distribution version, reported to clients.

    Returns an empty string when the package is run from a source checkout
    without being installed, which the SDK accepts.
    """
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("suryasiddhanta")
    except PackageNotFoundError:
        return ""


def tool_specs() -> List[Dict[str, Any]]:
    """
    The chatbot's tool definitions, read from the registry at call time.

    Read on every ``tools/list`` rather than cached at import, so the list
    always matches the registry ``dispatch_tool`` executes against.

    Returns:
        The ``TOOL_DEFINITIONS`` entries, each with ``name``, ``description``
        and ``input_schema`` (a JSON Schema object).
    """
    from suryasiddhanta.chatbot.tools import TOOL_DEFINITIONS

    return list(TOOL_DEFINITIONS)


def call_registry_tool(name: str, arguments: Dict[str, Any] | None) -> str:
    """
    Run one tool through the chatbot's dispatcher.

    Args:
        name: Tool name as listed by :func:`tool_specs`.
        arguments: The tool's input object; ``None`` is treated as ``{}``.

    Returns:
        The dispatcher's JSON string: the tool's result, or an object with an
        ``error`` key for an unknown tool or a tool that raised.
    """
    from suryasiddhanta.chatbot.tools import dispatch_tool

    return dispatch_tool(name, dict(arguments or {}))


def _is_error_payload(payload: str) -> bool:
    """
    Whether a dispatcher result is its error object.

    ``dispatch_tool`` reports failures as a top-level JSON object with an
    ``error`` key rather than raising; MCP wants such results flagged with
    ``isError`` so the client's model can see the call failed and retry.

    Args:
        payload: The dispatcher's JSON string.

    Returns:
        True when the payload parses to a dict containing ``error``.
    """
    try:
        parsed = json.loads(payload)
    except (TypeError, ValueError):
        return False
    return isinstance(parsed, dict) and "error" in parsed


def build_server() -> "Server":
    """
    Build the low-level MCP server over the chatbot tool registry.

    Uses the SDK's low-level ``Server`` with one ``tools/list`` and one
    ``tools/call`` handler instead of a decorator per tool, so the tool set
    is whatever the registry holds when a client asks.

    Returns:
        An ``mcp.server.Server`` ready for ``run()`` on any transport.

    Raises:
        RuntimeError: When the ``mcp`` extra is not installed.
    """
    try:
        import anyio
        import mcp.types as types
        from mcp.server import Server, ServerRequestContext
    except ImportError as exc:  # pragma: no cover - exercised without the extra
        raise RuntimeError(_MISSING_SDK_MESSAGE) from exc

    async def list_tools(
        ctx: ServerRequestContext[Any], params: types.PaginatedRequestParams | None
    ) -> types.ListToolsResult:
        """
        Answer ``tools/list`` with every registry tool, unpaginated.

        Args:
            ctx: Request context (unused).
            params: Pagination parameters (unused; the list is short enough
                to return in one page).

        Returns:
            One ``Tool`` per registry entry, ``input_schema`` passed through.
        """
        return types.ListToolsResult(
            tools=[
                types.Tool(
                    name=spec["name"],
                    description=spec.get("description"),
                    input_schema=spec["input_schema"],
                )
                for spec in tool_specs()
            ]
        )

    async def call_tool(
        ctx: ServerRequestContext[Any], params: types.CallToolRequestParams
    ) -> types.CallToolResult:
        """
        Answer ``tools/call`` by running the tool through ``dispatch_tool``.

        The calculation is synchronous and can take a moment (searches over
        days, corpus indexing), so it runs in a worker thread to keep the
        event loop free for pings and cancellation.

        Args:
            ctx: Request context (unused).
            params: The tool name and its arguments.

        Returns:
            The dispatcher's JSON string as a single text block, with
            ``is_error`` set when it is the dispatcher's error object.
        """
        payload = await anyio.to_thread.run_sync(
            call_registry_tool, params.name, params.arguments
        )
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=payload)],
            is_error=_is_error_payload(payload),
        )

    return Server(
        SERVER_NAME,
        version=_server_version(),
        instructions=SERVER_INSTRUCTIONS,
        on_list_tools=list_tools,
        on_call_tool=call_tool,
    )


async def serve_stdio(server: "Server") -> None:
    """
    Serve ``server`` over stdio until the client closes the connection.

    Args:
        server: A server from :func:`build_server`.
    """
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


def main() -> None:
    """
    Entry point for ``python -m suryasiddhanta.mcp_server``.

    Exits with the install hint, not a traceback, when the ``mcp`` extra is
    missing. Nothing is printed to stdout: on stdio it carries the protocol.
    """
    try:
        server = build_server()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from None

    import anyio

    anyio.run(serve_stdio, server)


if __name__ == "__main__":
    main()
