"""Pytest configuration and shared fixtures for e2e tests.

This module provides fixtures for end-to-end testing of the SVG-MCP server,
including server startup, client connections, and test workspace management.
"""

import subprocess
import time
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture(scope="session")
def e2e_fixtures_dir() -> Path:
    """Return the path to the e2e test fixtures directory."""
    return Path(__file__).parent.parent / "fixtures" / "e2e"


@pytest.fixture(scope="session")
def ai_generated_fixtures_dir(e2e_fixtures_dir: Path) -> Path:
    """Return the path to AI-generated SVG fixtures."""
    return e2e_fixtures_dir / "ai_generated"


@pytest.fixture(scope="session")
def complex_fixtures_dir(e2e_fixtures_dir: Path) -> Path:
    """Return the path to complex SVG fixtures."""
    return e2e_fixtures_dir / "complex"


@pytest.fixture(scope="session")
def edge_cases_fixtures_dir(e2e_fixtures_dir: Path) -> Path:
    """Return the path to edge case SVG fixtures."""
    return e2e_fixtures_dir / "edge_cases"


@pytest.fixture(scope="session")
def expected_outputs_dir(e2e_fixtures_dir: Path) -> Path:
    """Return the path to expected output fixtures."""
    return e2e_fixtures_dir / "expected_outputs"


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    """Create a temporary workspace for e2e tests.

    Returns:
        Path to the temporary workspace directory.
    """
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


@pytest.fixture
def temp_svg_file(temp_workspace: Path) -> Path:
    """Create a temporary SVG file for testing.

    Returns:
        Path to the temporary SVG file.
    """
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect width="100" height="100" fill="red"/>
</svg>"""
    svg_file = temp_workspace / "test.svg"
    svg_file.write_text(svg_content)
    return svg_file


@pytest.fixture(scope="session")
def sse_server_port() -> int:
    """Return a port number for the SSE server.

    Uses a fixed port for session-scoped tests.
    """
    return 8765


@pytest.fixture(scope="function")
def sse_server(
    sse_server_port: int,
) -> Generator[dict, None, None]:
    """Start MCP server with SSE transport for e2e tests.

    This fixture starts the server in a subprocess and waits for it to be ready.
    The server is terminated after the test completes.

    Yields:
        Dictionary with server connection information.
    """
    # Start server in background
    proc = subprocess.Popen(
        [
            "poetry",
            "run",
            "svg-mcp",
            "serve",
            "--transport",
            "sse",
            "--port",
            str(sse_server_port),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=Path(__file__).parent.parent.parent,
    )

    # Wait for server to be ready
    time.sleep(2)

    # Check if server started successfully
    if proc.poll() is not None:
        stdout, stderr = proc.communicate()
        raise RuntimeError(
            f"Server failed to start:\nstdout: {stdout.decode()}\nstderr: {stderr.decode()}"
        )

    yield {"host": "localhost", "port": sse_server_port, "process": proc}

    # Cleanup
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


@pytest.fixture
def cli_runner():
    """Create a Click CLI test runner.

    Returns:
        CliRunner instance for testing CLI commands.
    """
    from click.testing import CliRunner

    return CliRunner()


# Sample SVG content fixtures for e2e tests


@pytest.fixture
def simple_svg() -> str:
    """Return a simple valid SVG."""
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect width="100" height="100" fill="red"/>
</svg>"""


@pytest.fixture
def complex_svg() -> str:
    """Return a complex SVG with multiple elements."""
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ff0000"/>
      <stop offset="100%" stop-color="#0000ff"/>
    </linearGradient>
  </defs>
  <rect x="10" y="10" width="80" height="80" fill="url(#grad1)"/>
  <circle cx="150" cy="50" r="40" fill="#00ff00" opacity="0.7"/>
  <text x="100" y="150" text-anchor="middle" font-size="16">Hello World</text>
  <path d="M 10 180 Q 100 120 190 180" stroke="#333" fill="none" stroke-width="2"/>
</svg>"""


@pytest.fixture
def invalid_svg() -> str:
    """Return an invalid SVG with syntax errors."""
    return """<svg xmlns="http://www.w3.org/2000/svg">
  <rect width="100" height="100"
</svg>"""


@pytest.fixture
def svg_with_unicode() -> str:
    """Return an SVG with Unicode text content."""
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 100">
  <text x="10" y="30" font-size="14">Hello 世界 🌍</text>
  <text x="10" y="60" font-size="14">مرحبا بالعالم</text>
  <text x="10" y="90" font-size="14">Привет мир</text>
</svg>"""


@pytest.fixture
def large_svg() -> str:
    """Return a large SVG with many elements.

    Generates an SVG with 1000 rectangles for performance testing.
    """
    elements = []
    for i in range(1000):
        x = (i % 50) * 20
        y = (i // 50) * 20
        color = f"#{(i * 37) % 256:02x}{(i * 73) % 256:02x}{(i * 113) % 256:02x}"
        elements.append(
            f'  <rect x="{x}" y="{y}" width="18" height="18" fill="{color}"/>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 400">
{chr(10).join(elements)}
</svg>"""


@pytest.fixture
def deeply_nested_svg() -> str:
    """Return an SVG with deeply nested elements.

    Creates 50 levels of nested groups for edge case testing.
    """
    content = '<rect width="10" height="10" fill="red"/>'
    for i in range(50):
        content = f'<g id="level{i}">{content}</g>'

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  {content}
</svg>"""


@pytest.fixture
def svg_pair_original() -> str:
    """Return the original SVG for diff testing."""
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="10" y="10" width="30" height="30" fill="blue"/>
  <circle cx="70" cy="50" r="20" fill="green"/>
</svg>"""


@pytest.fixture
def svg_pair_modified() -> str:
    """Return a modified SVG for diff testing."""
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="20" y="10" width="30" height="30" fill="red"/>
  <circle cx="70" cy="50" r="25" fill="green"/>
</svg>"""
