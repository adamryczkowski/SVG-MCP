"""Pytest configuration and shared fixtures for SVG-MCP tests."""

from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def valid_fixtures_dir(fixtures_dir: Path) -> Path:
    """Return the path to valid SVG fixtures."""
    return fixtures_dir / "valid"


@pytest.fixture
def invalid_fixtures_dir(fixtures_dir: Path) -> Path:
    """Return the path to invalid SVG fixtures."""
    return fixtures_dir / "invalid"


@pytest.fixture
def pairs_fixtures_dir(fixtures_dir: Path) -> Path:
    """Return the path to SVG pair fixtures for diff testing."""
    return fixtures_dir / "pairs"


@pytest.fixture
def minimal_svg(valid_fixtures_dir: Path) -> str:
    """Return the content of minimal.svg fixture."""
    return (valid_fixtures_dir / "minimal.svg").read_text()


@pytest.fixture
def complex_svg(valid_fixtures_dir: Path) -> str:
    """Return the content of complex.svg fixture."""
    return (valid_fixtures_dir / "complex.svg").read_text()


@pytest.fixture
def malformed_svg(invalid_fixtures_dir: Path) -> str:
    """Return the content of malformed.svg fixture."""
    return (invalid_fixtures_dir / "malformed.svg").read_text()


@pytest.fixture
def missing_namespace_svg(invalid_fixtures_dir: Path) -> str:
    """Return the content of missing_namespace.svg fixture."""
    return (invalid_fixtures_dir / "missing_namespace.svg").read_text()


@pytest.fixture
def unclosed_tag_svg(invalid_fixtures_dir: Path) -> str:
    """Return the content of unclosed_tag.svg fixture."""
    return (invalid_fixtures_dir / "unclosed_tag.svg").read_text()


@pytest.fixture
def not_svg(invalid_fixtures_dir: Path) -> str:
    """Return the content of not_svg.svg fixture (HTML file)."""
    return (invalid_fixtures_dir / "not_svg.svg").read_text()


@pytest.fixture
def rect_original_svg(pairs_fixtures_dir: Path) -> str:
    """Return the content of rect_original.svg fixture."""
    return (pairs_fixtures_dir / "rect_original.svg").read_text()


@pytest.fixture
def rect_moved_svg(pairs_fixtures_dir: Path) -> str:
    """Return the content of rect_moved.svg fixture."""
    return (pairs_fixtures_dir / "rect_moved.svg").read_text()


@pytest.fixture
def rect_color_changed_svg(pairs_fixtures_dir: Path) -> str:
    """Return the content of rect_color_changed.svg fixture."""
    return (pairs_fixtures_dir / "rect_color_changed.svg").read_text()


@pytest.fixture
def circle_original_svg(pairs_fixtures_dir: Path) -> str:
    """Return the content of circle_original.svg fixture."""
    return (pairs_fixtures_dir / "circle_original.svg").read_text()


@pytest.fixture
def circle_resized_svg(pairs_fixtures_dir: Path) -> str:
    """Return the content of circle_resized.svg fixture."""
    return (pairs_fixtures_dir / "circle_resized.svg").read_text()


@pytest.fixture
def tmp_output_dir(tmp_path: Path) -> Path:
    """Return a temporary directory for test output files."""
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir
