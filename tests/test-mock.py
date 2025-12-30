"""Smoke tests for SVG_MCP package exports."""

from SVG_MCP import (
    SVGDiffer,
    SVGRenderer,
    SVGValidator,
    __version__,
    create_server,
)


def test_package_exports_validator():
    """Test that SVGValidator is exported and can be instantiated."""
    validator = SVGValidator()
    assert validator is not None


def test_package_exports_renderer():
    """Test that SVGRenderer is exported and can be instantiated."""
    renderer = SVGRenderer()
    assert renderer is not None


def test_package_exports_differ():
    """Test that SVGDiffer is exported and can be instantiated."""
    differ = SVGDiffer()
    assert differ is not None


def test_package_exports_create_server():
    """Test that create_server is exported and returns a server."""
    server = create_server()
    assert server is not None
    assert server.name == "SVG-MCP"


def test_package_exports_version():
    """Test that __version__ is exported and is a valid version string."""
    assert __version__ is not None
    assert isinstance(__version__, str)
    # Version should be in format X.Y.Z or X.Y.Z.dev
    parts = __version__.split(".")
    assert len(parts) >= 2
