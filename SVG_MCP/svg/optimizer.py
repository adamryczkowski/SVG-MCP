"""SVG optimizer using Scour.

This module provides a wrapper around Scour for SVG optimization with
preset support and validation integration.
"""

from pathlib import Path
from typing import Any

from scour import scour
from scour.scour import sanitizeOptions

from SVG_MCP.models.lint_types import OptimizePreset, OptimizeResult


# Optimization presets
OPTIMIZE_PRESETS: dict[OptimizePreset, dict[str, Any]] = {
    "safe": {
        # Conservative - keeps editor data, high precision
        "digits": 8,
        "cdigits": -1,  # Same as digits
        "keep_editor_data": True,
        "remove_metadata": False,
        "strip_comments": False,
        "remove_titles": False,
        "remove_descriptions": False,
        "enable_viewboxing": False,
        "shorten_ids": False,
        "strip_ids": False,
        "indent_type": "space",
        "indent_depth": 1,
        "newlines": True,
        "strip_xml_prolog": False,
        "renderer_workaround": True,
    },
    "default": {
        # Balanced - removes editor data, standard precision
        "digits": 5,
        "cdigits": -1,
        "keep_editor_data": False,
        "remove_metadata": False,
        "strip_comments": False,
        "remove_titles": False,
        "remove_descriptions": False,
        "enable_viewboxing": False,
        "shorten_ids": False,
        "strip_ids": False,
        "indent_type": "space",
        "indent_depth": 1,
        "newlines": True,
        "strip_xml_prolog": False,
        "renderer_workaround": True,
    },
    "maximum": {
        # Aggressive - removes everything, low precision, minified
        "digits": 3,
        "cdigits": -1,
        "keep_editor_data": False,
        "remove_metadata": True,
        "strip_comments": True,
        "remove_titles": True,
        "remove_descriptions": True,
        "enable_viewboxing": True,
        "shorten_ids": True,
        "strip_ids": True,
        "indent_type": "none",
        "indent_depth": 0,
        "newlines": False,
        "strip_xml_prolog": True,
        "renderer_workaround": True,
    },
}


class SVGOptimizer:
    """SVG optimizer using Scour."""

    def __init__(self, preset: OptimizePreset = "default"):
        """Initialize the optimizer with a preset.

        Args:
            preset: Optimization preset to use ('safe', 'default', 'maximum')
        """
        self.preset = preset
        self._base_options = OPTIMIZE_PRESETS.get(preset, OPTIMIZE_PRESETS["default"])

    def optimize(
        self,
        content: str,
        *,
        precision: int | None = None,
        remove_editor_data: bool | None = None,
        remove_metadata: bool | None = None,
        remove_comments: bool | None = None,
        remove_titles: bool | None = None,
        remove_descriptions: bool | None = None,
        enable_viewboxing: bool | None = None,
        shorten_ids: bool | None = None,
        strip_ids: bool | None = None,
        indent: str | None = None,
        no_line_breaks: bool | None = None,
        strip_xml_prolog: bool | None = None,
        renderer_workaround: bool | None = None,
    ) -> OptimizeResult:
        """Optimize SVG content.

        Args:
            content: SVG content to optimize
            precision: Number of significant digits for coordinates (1-8)
            remove_editor_data: Remove Inkscape/Sodipodi/Adobe metadata
            remove_metadata: Remove <metadata> elements
            remove_comments: Remove XML comments
            remove_titles: Remove <title> elements
            remove_descriptions: Remove <desc> elements
            enable_viewboxing: Convert width/height to viewBox
            shorten_ids: Shorten element IDs
            strip_ids: Remove unreferenced IDs
            indent: Indentation style ('none', 'space', 'tab')
            no_line_breaks: Remove line breaks (minify)
            strip_xml_prolog: Remove XML prolog
            renderer_workaround: Apply librsvg workarounds

        Returns:
            OptimizeResult with optimization details
        """
        original_size = len(content.encode("utf-8"))

        try:
            # Build options from preset and overrides
            options = self._build_options(
                precision=precision,
                remove_editor_data=remove_editor_data,
                remove_metadata=remove_metadata,
                remove_comments=remove_comments,
                remove_titles=remove_titles,
                remove_descriptions=remove_descriptions,
                enable_viewboxing=enable_viewboxing,
                shorten_ids=shorten_ids,
                strip_ids=strip_ids,
                indent=indent,
                no_line_breaks=no_line_breaks,
                strip_xml_prolog=strip_xml_prolog,
                renderer_workaround=renderer_workaround,
            )

            # Run Scour
            optimized_content = scour.scourString(content, options)

            optimized_size = len(optimized_content.encode("utf-8"))
            reduction_percent = (
                ((original_size - optimized_size) / original_size) * 100
                if original_size > 0
                else 0.0
            )

            return OptimizeResult(
                success=True,
                optimized_content=optimized_content,
                original_size=original_size,
                optimized_size=optimized_size,
                reduction_percent=round(reduction_percent, 2),
                error=None,
            )

        except Exception as e:
            return OptimizeResult(
                success=False,
                optimized_content=None,
                original_size=original_size,
                optimized_size=None,
                reduction_percent=None,
                error=str(e),
            )

    def optimize_file(
        self,
        file_path: Path,
        **kwargs: Any,
    ) -> OptimizeResult:
        """Optimize an SVG file.

        Args:
            file_path: Path to the SVG file to optimize
            **kwargs: Additional options to pass to optimize()

        Returns:
            OptimizeResult with optimization details
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            return self.optimize(content, **kwargs)
        except OSError as e:
            return OptimizeResult(
                success=False,
                optimized_content=None,
                original_size=0,
                optimized_size=None,
                reduction_percent=None,
                error=f"Failed to read file: {e}",
            )

    def _build_options(
        self,
        precision: int | None = None,
        remove_editor_data: bool | None = None,
        remove_metadata: bool | None = None,
        remove_comments: bool | None = None,
        remove_titles: bool | None = None,
        remove_descriptions: bool | None = None,
        enable_viewboxing: bool | None = None,
        shorten_ids: bool | None = None,
        strip_ids: bool | None = None,
        indent: str | None = None,
        no_line_breaks: bool | None = None,
        strip_xml_prolog: bool | None = None,
        renderer_workaround: bool | None = None,
    ) -> Any:
        """Build Scour options from preset and overrides.

        Returns a sanitized options object for Scour.
        """
        # Start with preset options
        opts: dict[str, Any] = dict(self._base_options)

        # Apply overrides
        if precision is not None:
            opts["digits"] = max(1, min(8, precision))

        if remove_editor_data is not None:
            opts["keep_editor_data"] = not remove_editor_data

        if remove_metadata is not None:
            opts["remove_metadata"] = remove_metadata

        if remove_comments is not None:
            opts["strip_comments"] = remove_comments

        if remove_titles is not None:
            opts["remove_titles"] = remove_titles

        if remove_descriptions is not None:
            opts["remove_descriptions"] = remove_descriptions

        if enable_viewboxing is not None:
            opts["enable_viewboxing"] = enable_viewboxing

        if shorten_ids is not None:
            opts["shorten_ids"] = shorten_ids

        if strip_ids is not None:
            opts["strip_ids"] = strip_ids

        if indent is not None:
            if indent == "none":
                opts["indent_type"] = "none"
                opts["indent_depth"] = 0
            elif indent == "tab":
                opts["indent_type"] = "tab"
                opts["indent_depth"] = 1
            else:  # space
                opts["indent_type"] = "space"
                opts["indent_depth"] = 1

        if no_line_breaks is not None:
            opts["newlines"] = not no_line_breaks

        if strip_xml_prolog is not None:
            opts["strip_xml_prolog"] = strip_xml_prolog

        if renderer_workaround is not None:
            opts["renderer_workaround"] = renderer_workaround

        # Create an options object that Scour expects
        # Scour uses optparse.Values-like objects
        class ScourOptions:
            pass

        scour_opts = ScourOptions()
        for key, value in opts.items():
            setattr(scour_opts, key, value)

        # Sanitize options to fill in defaults
        return sanitizeOptions(scour_opts)


def optimize_svg(
    content: str,
    preset: OptimizePreset = "default",
    **kwargs: Any,
) -> OptimizeResult:
    """Convenience function to optimize SVG content.

    Args:
        content: SVG content to optimize
        preset: Optimization preset ('safe', 'default', 'maximum')
        **kwargs: Additional options to pass to SVGOptimizer.optimize()

    Returns:
        OptimizeResult with optimization details
    """
    optimizer = SVGOptimizer(preset=preset)
    return optimizer.optimize(content, **kwargs)
