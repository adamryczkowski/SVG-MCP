# Implementation Plan: Shared MCP Server Architecture

## Selected Strategy

Based on the analysis in [fastmcp-cpu-usage-plan.md](./fastmcp-cpu-usage-plan.md), we are implementing **Strategy 3: Shared Server Architecture** using Streamable HTTP transport.

This strategy provides the highest impact with reasonable effort by reducing the number of MCP server instances from N (one per VS Code window) to 1 shared instance.

## Goals

1. Reduce idle CPU usage from ~20% (14 instances) to ~1.3% (1 instance)
2. Maintain full functionality of MCP tools
3. Enable multiple VS Code windows to share a single MCP server
4. Provide easy startup/shutdown management

## Prerequisites

- FastMCP 2.14.2 or later (already installed)
- VS Code with Roo Code extension (supports Streamable HTTP transport)
- systemd (for service management on Linux)

## Implementation Steps

### Step 1: Create Server Entry Point for HTTP Transport

Create a new entry point script that runs the MCP server with HTTP transport instead of stdio.

**File:** `scripts/run-svg-mcp-http.py`

```python
#!/usr/bin/env python3
"""Run SVG-MCP server with HTTP transport for shared access."""

import argparse
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from SVG_MCP import create_server  # Adjust import based on actual structure


def main():
    parser = argparse.ArgumentParser(description="Run SVG-MCP server with HTTP transport")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8081, help="Port to bind to")
    parser.add_argument("--log-level", default="info", help="Log level")
    args = parser.parse_args()

    server = create_server()
    server.run(
        transport="streamable-http",
        host=args.host,
        port=args.port,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
```

### Step 2: Add justfile Actions

Add convenient commands to start/stop the shared server.

**Add to:** `justfile`

```just
# Run SVG-MCP server with HTTP transport (shared mode)
run-svg-mcp-http host="127.0.0.1" port="8081":
    poetry run python scripts/run-svg-mcp-http.py --host {{host}} --port {{port}}

# Check if SVG-MCP HTTP server is running
svg-mcp-status:
    @curl -s http://127.0.0.1:8081/mcp/health || echo "Server not running"
```

### Step 3: Create systemd Service File (Optional)

For persistent server management, create a systemd user service.

**File:** `scripts/svg-mcp.service`

```ini
[Unit]
Description=SVG-MCP Server (Shared HTTP Mode)
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/adam/tmp/SVG-MCP
ExecStart=/home/adam/.local/bin/poetry run python scripts/run-svg-mcp-http.py --host 127.0.0.1 --port 8081
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
```

**Installation commands:**
```bash
# Create user systemd directory if it doesn't exist
mkdir -p ~/.config/systemd/user/

# Copy service file
cp scripts/svg-mcp.service ~/.config/systemd/user/

# Reload systemd
systemctl --user daemon-reload

# Enable and start the service
systemctl --user enable svg-mcp
systemctl --user start svg-mcp

# Check status
systemctl --user status svg-mcp
```

### Step 4: Update VS Code MCP Configuration

Configure VS Code to use the shared HTTP server instead of spawning individual stdio processes.

**File:** `.vscode/mcp.json` (or global settings)

**Before (stdio transport - spawns new process per window):**
```json
{
  "servers": {
    "svg-mcp": {
      "command": "poetry",
      "args": ["run", "svg-mcp", "serve"],
      "cwd": "/home/adam/tmp/SVG-MCP"
    }
  }
}
```

**After (streamable-http transport - connects to shared server):**
```json
{
  "servers": {
    "svg-mcp": {
      "type": "streamable-http",
      "url": "http://127.0.0.1:8081/mcp"
    }
  }
}
```

### Step 5: Add Health Check Endpoint (Optional)

Add a health check endpoint to the server for monitoring.

**Modify:** Server initialization to add custom route

```python
from starlette.responses import JSONResponse

@server.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "healthy", "server": "svg-mcp"})
```

### Step 6: Documentation Update

Update the project README to document the new shared server mode.

**Add to:** `README.md`

```markdown
## Running Modes

### Stdio Mode (Default)
Each VS Code window spawns its own server process:
```bash
poetry run svg-mcp serve
```

### Shared HTTP Mode (Recommended for multiple windows)
Run a single shared server that all VS Code windows connect to:
```bash
# Start the shared server
just run-svg-mcp-http

# Or use systemd for persistent service
systemctl --user start svg-mcp
```

Configure VS Code to use the shared server by updating `.vscode/mcp.json`:
```json
{
  "servers": {
    "svg-mcp": {
      "type": "streamable-http",
      "url": "http://127.0.0.1:8081/mcp"
    }
  }
}
```
```

## Testing Plan

### Unit Tests
1. Verify server starts correctly with HTTP transport
2. Verify health check endpoint responds

### Integration Tests
1. Start server with HTTP transport
2. Connect multiple clients simultaneously
3. Verify all MCP tools work correctly
4. Verify server handles client disconnections gracefully

### Performance Tests
1. Measure CPU usage with shared server (should be ~1.3%)
2. Compare with multiple stdio instances
3. Verify response latency is acceptable

## Rollback Plan

If issues arise with the shared server approach:

1. Stop the shared server:
   ```bash
   systemctl --user stop svg-mcp
   ```

2. Revert VS Code configuration to stdio transport:
   ```json
   {
     "servers": {
       "svg-mcp": {
         "command": "poetry",
         "args": ["run", "svg-mcp", "serve"],
         "cwd": "/home/adam/tmp/SVG-MCP"
       }
     }
   }
   ```

3. Restart VS Code

## Success Criteria

- [ ] Shared server starts successfully with HTTP transport
- [ ] Multiple VS Code windows can connect to the same server
- [ ] All MCP tools function correctly
- [ ] Idle CPU usage reduced from ~20% to ~2-3%
- [ ] Server handles client reconnections gracefully
- [ ] Documentation updated

## Timeline

| Task | Estimated Time |
|------|----------------|
| Step 1: Create entry point script | 30 minutes |
| Step 2: Add justfile actions | 15 minutes |
| Step 3: Create systemd service | 30 minutes |
| Step 4: Update VS Code config | 15 minutes |
| Step 5: Add health check | 15 minutes |
| Step 6: Update documentation | 30 minutes |
| Testing | 1 hour |
| **Total** | **~3.5 hours** |

## References

- [Roo Code MCP Transports Documentation](https://docs.roocode.com/features/mcp/transports)
- [FastMCP HTTP Transport](https://gofastmcp.com/servers/transports#http-transport)
- [systemd User Services](https://wiki.archlinux.org/title/Systemd/User)

## Document History

| Date | Author | Description |
|------|--------|-------------|
| 2025-12-25 | AI Assistant | Initial implementation plan created |
