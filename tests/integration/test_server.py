"""Integration tests for MCP server."""

from SVG_MCP.server import create_server, mcp


class TestServerInitialization:
    """Tests for server initialization."""

    def test_server_initialization(self) -> None:
        """Test that server initializes correctly."""
        server = create_server()
        assert server is not None
        assert server.name == "SVG-MCP"

    def test_server_has_tools(self) -> None:
        """Test that server has all expected tools registered."""
        server = create_server()
        tool_names = [t.name for t in server._tool_manager._tools.values()]

        assert "svg_validate" in tool_names
        assert "svg_render" in tool_names
        assert "svg_diff" in tool_names
        assert "svg_edit" in tool_names

    def test_server_tool_count(self) -> None:
        """Test that server has exactly 4 tools."""
        server = create_server()
        tool_count = len(server._tool_manager._tools)
        assert tool_count == 4


class TestServerToolSchemas:
    """Tests for tool schemas."""

    def test_svg_validate_schema(self) -> None:
        """Test svg_validate tool has correct schema."""
        server = create_server()
        tools = {t.name: t for t in server._tool_manager._tools.values()}

        validate_tool = tools.get("svg_validate")
        assert validate_tool is not None
        assert validate_tool.description is not None
        assert "validate" in validate_tool.description.lower()

    def test_svg_render_schema(self) -> None:
        """Test svg_render tool has correct schema."""
        server = create_server()
        tools = {t.name: t for t in server._tool_manager._tools.values()}

        render_tool = tools.get("svg_render")
        assert render_tool is not None
        assert render_tool.description is not None
        assert "render" in render_tool.description.lower()

    def test_svg_diff_schema(self) -> None:
        """Test svg_diff tool has correct schema."""
        server = create_server()
        tools = {t.name: t for t in server._tool_manager._tools.values()}

        diff_tool = tools.get("svg_diff")
        assert diff_tool is not None
        assert diff_tool.description is not None
        assert (
            "diff" in diff_tool.description.lower()
            or "compare" in diff_tool.description.lower()
        )

    def test_svg_edit_schema(self) -> None:
        """Test svg_edit tool has correct schema."""
        server = create_server()
        tools = {t.name: t for t in server._tool_manager._tools.values()}

        edit_tool = tools.get("svg_edit")
        assert edit_tool is not None
        assert edit_tool.description is not None
        assert "edit" in edit_tool.description.lower()


class TestServerResources:
    """Tests for server resources."""

    def test_server_has_resources(self) -> None:
        """Test that server has resources registered."""
        server = create_server()
        # Resources are registered with templates
        assert server._resource_manager is not None


class TestServerModuleImport:
    """Tests for module import."""

    def test_mcp_instance_exists(self) -> None:
        """Test that mcp instance is exported."""
        assert mcp is not None
        assert mcp.name == "SVG-MCP"

    def test_create_server_returns_same_instance(self) -> None:
        """Test that create_server returns the same mcp instance."""
        server = create_server()
        assert server is mcp
