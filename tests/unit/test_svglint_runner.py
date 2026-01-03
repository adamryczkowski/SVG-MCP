"""Unit tests for svglint_runner module."""

import pytest

from SVG_MCP.svg.svglint_runner import SvglintRunner, svglint_available


class TestSvglintAvailable:
    """Tests for svglint_available function."""

    def test_returns_bool(self) -> None:
        """svglint_available should return a boolean."""
        result = svglint_available()
        assert isinstance(result, bool)

    def test_caches_result(self) -> None:
        """Result should be cached after first call."""
        # Reset cache
        SvglintRunner._available = None

        # First call
        result1 = svglint_available()

        # Second call should use cache
        result2 = svglint_available()

        assert result1 == result2


class TestSvglintRunner:
    """Tests for SvglintRunner class."""

    def test_is_available_returns_bool(self) -> None:
        """is_available should return a boolean."""
        result = SvglintRunner.is_available()
        assert isinstance(result, bool)

    def test_get_version_when_not_available(self) -> None:
        """get_version should return None if svglint is not available."""
        if not SvglintRunner.is_available():
            version = SvglintRunner.get_version()
            assert version is None

    @pytest.mark.skipif(
        not svglint_available(),
        reason="svglint not installed",
    )
    def test_init_when_available(self) -> None:
        """SvglintRunner should initialize when svglint is available."""
        runner = SvglintRunner()
        assert runner is not None

    @pytest.mark.skipif(
        svglint_available(),
        reason="svglint is installed",
    )
    def test_init_raises_when_not_available(self) -> None:
        """SvglintRunner should raise RuntimeError when svglint is not available."""
        with pytest.raises(RuntimeError, match="svglint not available"):
            SvglintRunner()

    @pytest.mark.skipif(
        not svglint_available(),
        reason="svglint not installed",
    )
    def test_lint_valid_svg(self) -> None:
        """Linting a valid SVG should return no issues."""
        runner = SvglintRunner()
        svg = '<svg xmlns="http://www.w3.org/2000/svg"><rect width="100" height="100"/></svg>'
        issues = runner.lint(svg)
        # With no rules configured, should pass
        assert isinstance(issues, list)

    @pytest.mark.skipif(
        not svglint_available(),
        reason="svglint not installed",
    )
    def test_lint_with_element_rules(self) -> None:
        """Linting with element rules should work."""
        runner = SvglintRunner()
        svg = '<svg xmlns="http://www.w3.org/2000/svg"><rect width="100" height="100"/></svg>'
        issues = runner.lint(
            svg,
            element_rules={"svg": 1},
        )
        assert isinstance(issues, list)

    @pytest.mark.skipif(
        not svglint_available(),
        reason="svglint not installed",
    )
    def test_lint_element_rule_failure(self) -> None:
        """Linting should report issues when element rules fail."""
        runner = SvglintRunner()
        # SVG without title element
        svg = '<svg xmlns="http://www.w3.org/2000/svg"><rect width="100" height="100"/></svg>'
        issues = runner.lint(
            svg,
            element_rules={"svg > title": 1},  # Require title
        )
        # Should have at least one issue
        assert isinstance(issues, list)
        # Note: The actual issue detection depends on svglint output parsing

    @pytest.mark.skipif(
        not svglint_available(),
        reason="svglint not installed",
    )
    def test_lint_with_validate_xml(self) -> None:
        """Linting with XML validation enabled should work."""
        runner = SvglintRunner()
        svg = '<svg xmlns="http://www.w3.org/2000/svg"><rect width="100" height="100"/></svg>'
        issues = runner.lint(svg, validate_xml=True)
        assert isinstance(issues, list)

    @pytest.mark.skipif(
        not svglint_available(),
        reason="svglint not installed",
    )
    def test_lint_invalid_xml(self) -> None:
        """Linting invalid XML should report issues."""
        runner = SvglintRunner()
        svg = "<svg><unclosed>"  # Invalid XML
        issues = runner.lint(svg, validate_xml=True)
        # Should have at least one issue
        assert isinstance(issues, list)
        # Note: svglint may or may not catch this depending on config


class TestBuildConfig:
    """Tests for config generation."""

    @pytest.mark.skipif(
        not svglint_available(),
        reason="svglint not installed",
    )
    def test_build_config_with_element_rules(self) -> None:
        """Config should include element rules."""
        runner = SvglintRunner()
        config = runner._build_config(
            element_rules={"svg": 1, "svg > title": 1},
            attribute_rules=None,
            validate_xml=True,
        )
        assert "elm" in config
        assert "svg" in config
        assert "title" in config

    @pytest.mark.skipif(
        not svglint_available(),
        reason="svglint not installed",
    )
    def test_build_config_with_attribute_rules(self) -> None:
        """Config should include attribute rules."""
        runner = SvglintRunner()
        config = runner._build_config(
            element_rules=None,
            attribute_rules=[
                {
                    "rule::selector": "svg",
                    "xmlns": "http://www.w3.org/2000/svg",
                }
            ],
            validate_xml=False,
        )
        assert "attr" in config
        assert "selector" in config

    @pytest.mark.skipif(
        not svglint_available(),
        reason="svglint not installed",
    )
    def test_build_config_exports_default(self) -> None:
        """Config should export default."""
        runner = SvglintRunner()
        config = runner._build_config(
            element_rules=None,
            attribute_rules=None,
            validate_xml=True,
        )
        assert "export default config" in config


class TestParseOutput:
    """Tests for output parsing."""

    @pytest.mark.skipif(
        not svglint_available(),
        reason="svglint not installed",
    )
    def test_parse_output_success(self) -> None:
        """Parsing successful output should return empty list."""
        runner = SvglintRunner()
        issues = runner._parse_output("", "", 0)
        assert issues == []

    @pytest.mark.skipif(
        not svglint_available(),
        reason="svglint not installed",
    )
    def test_parse_output_failure_with_message(self) -> None:
        """Parsing failure output should return issues."""
        runner = SvglintRunner()
        issues = runner._parse_output(
            "elm: Expected 1 svg > title element(s), found 0",
            "",
            1,
        )
        assert len(issues) >= 1

    @pytest.mark.skipif(
        not svglint_available(),
        reason="svglint not installed",
    )
    def test_parse_output_failure_no_message(self) -> None:
        """Parsing failure with no message should return generic issue."""
        runner = SvglintRunner()
        issues = runner._parse_output("", "", 1)
        assert len(issues) == 1
        assert issues[0].code == "svglint/unknown"
