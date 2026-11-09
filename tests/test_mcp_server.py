"""Tests for the MCP server over the chatbot tool registry (``mcp_server.py``).

The server is driven through the SDK's in-process ``Client``, which speaks the
real protocol over memory streams, so these cover the wire shape a Claude
Desktop or Claude Code client sees without spawning a subprocess. Tool counts
are always read from ``TOOL_DEFINITIONS``: the registry grows, and the server
must follow it with no edit.
"""

import json
import sys

import pytest

# Skip before importing anything from the optional [mcp] stack: without it
# AnyIO may be missing too, and an unconditional import would fail collection.
pytest.importorskip("mcp")
anyio = pytest.importorskip("anyio")

from mcp import Client  # noqa: E402

from suryasiddhanta import mcp_server  # noqa: E402
from suryasiddhanta.chatbot.tools import TOOL_DEFINITIONS, dispatch_tool  # noqa: E402


def _run(fn, *args):
    """Run an async client scenario to completion and return its result."""
    return anyio.run(fn, *args)


async def _list_tools():
    """List the server's tools through an in-memory client session."""
    async with Client(mcp_server.build_server()) as client:
        return (await client.list_tools()).tools


async def _call_tool(name, arguments):
    """Call one tool through an in-memory client session."""
    async with Client(mcp_server.build_server()) as client:
        return await client.call_tool(name, arguments)


def test_list_tools_mirrors_registry():
    """
    ``tools/list`` returns exactly the registry's tools, in order.

    Expected: as many tools as ``TOOL_DEFINITIONS`` holds, with the same names
    in the same order, so no tool is dropped, duplicated or invented.
    """
    tools = _run(_list_tools)
    assert len(tools) == len(TOOL_DEFINITIONS)
    assert [t.name for t in tools] == [d["name"] for d in TOOL_DEFINITIONS]


def test_list_tools_passes_schema_and_description_through():
    """
    Each listed tool carries its registry description and input schema unchanged.

    Expected: ``description`` and ``inputSchema`` equal the registry entry's
    ``description`` and ``input_schema`` for every tool, so an MCP client
    validates and documents arguments exactly as the in-process agent does.
    """
    tools = {t.name: t for t in _run(_list_tools)}
    for spec in TOOL_DEFINITIONS:
        tool = tools[spec["name"]]
        assert tool.description == spec["description"]
        assert tool.input_schema == spec["input_schema"]


def test_call_tool_round_trip_matches_dispatcher():
    """
    ``tools/call`` on ``compute_panchanga`` returns the dispatcher's JSON as text.

    Expected: one text block that parses as a JSON object without an
    ``error`` key, identical to calling ``dispatch_tool`` in-process with the
    same arguments, and the result is not flagged as an error.
    """
    args = {"year": 2024, "month": 1, "day": 1}
    result = _run(_call_tool, "compute_panchanga", args)

    assert not result.is_error
    assert len(result.content) == 1
    text = result.content[0].text
    payload = json.loads(text)
    assert isinstance(payload, dict) and "error" not in payload
    assert payload == json.loads(dispatch_tool("compute_panchanga", args))


def test_unknown_tool_returns_dispatcher_error():
    """
    Calling a tool the registry does not have returns the dispatcher's error JSON.

    Expected: a normal result (not a protocol error) whose text is exactly
    what ``dispatch_tool`` returns for an unknown name, flagged ``is_error``
    so the client's model sees the call failed.
    """
    result = _run(_call_tool, "no_such_tool", {})

    assert result.is_error
    assert result.content[0].text == dispatch_tool("no_such_tool", {})
    assert json.loads(result.content[0].text) == {"error": "Unknown tool: no_such_tool"}


def test_build_server_without_sdk_raises_install_hint(monkeypatch):
    """
    Building the server without the ``mcp`` extra fails with a clear message.

    Expected: ``build_server`` raises ``RuntimeError`` whose message names the
    ``.[mcp]`` extra, rather than surfacing a bare ``ImportError``.
    """
    for module in ("mcp", "mcp.types", "mcp.server"):
        monkeypatch.setitem(sys.modules, module, None)

    with pytest.raises(RuntimeError, match=r'pip install -e "\.\[mcp\]"'):
        mcp_server.build_server()
