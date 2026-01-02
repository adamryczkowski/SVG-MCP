# Plan to Address FastMCP Idle CPU Usage Issue

## Problem Summary

MCP servers built with `fastmcp` consume excessive CPU (~1.3% per instance) while idle, due to a busy-polling pattern in the asyncio event loop. With multiple VS Code windows open, each spawning its own MCP server instances, this leads to significant cumulative CPU usage (18-20% with 14 instances).

### Root Cause

Based on `strace` analysis, the idle server makes:
- ~1000 `clock_gettime` calls per second
- ~200 `epoll_wait` calls per second

This indicates the asyncio event loop is spinning continuously rather than sleeping efficiently while waiting for incoming requests.

### Technology Stack

| Component | Version |
|-----------|---------|
| fastmcp | 2.14.2 |
| Python | 3.12 |
| Transport | stdio (for VS Code MCP servers) |

---

## Alternative Strategies

### Strategy 1: Report Issue to FastMCP/MCP SDK Maintainers

**Description:**
The busy-polling behavior appears to originate from the underlying MCP SDK's stdio transport implementation (`mcp.server.stdio.stdio_server()`). FastMCP wraps this SDK, so the issue may need to be fixed upstream.

**Approach:**
1. Create a minimal reproducible example demonstrating the CPU usage issue
2. File an issue on the [fastmcp GitHub repository](https://github.com/jlowin/fastmcp)
3. Also file an issue on the [MCP SDK repository](https://github.com/modelcontextprotocol/python-sdk) if the root cause is in the SDK
4. Include `strace` output and CPU profiling data
5. Monitor for upstream fixes and update dependencies when available

**Pros:**
- Fixes the root cause for all users of fastmcp/MCP SDK
- No local code changes required (once fixed upstream)
- Maintainers have deeper knowledge of the codebase

**Cons:**
- Dependent on upstream maintainers' response time
- May take weeks or months to get a fix
- Temporary workarounds may still be needed

**Effort:** Low (1-2 hours to file issues)
**Impact:** High (fixes root cause)
**Timeline:** Unknown (depends on upstream)

---

### Strategy 2: Implement Custom Event Loop Configuration

**Description:**
Configure the asyncio event loop to use more efficient polling settings. The busy-polling may be caused by default event loop settings that are optimized for low latency rather than low CPU usage.

**Approach:**
1. Investigate `uvloop` as an alternative event loop (known for better performance)
2. Configure `anyio` backend settings to reduce polling frequency
3. Add sleep intervals in the message processing loop
4. Use `asyncio.set_event_loop_policy()` to configure custom settings

**Implementation:**
```python
# Option A: Use uvloop for better event loop performance
import uvloop
uvloop.install()

# Option B: Configure anyio to use different backend settings
import anyio
# Set backend-specific options

# Option C: Patch the message processing loop to add sleep
# This would require modifying how we call fastmcp
```

**Pros:**
- Can be implemented locally without waiting for upstream
- May provide immediate relief
- uvloop is a well-tested alternative

**Cons:**
- May not address the root cause if it's in the MCP SDK
- Adds dependency on uvloop
- May affect server responsiveness

**Effort:** Medium (4-8 hours)
**Impact:** Medium to High
**Timeline:** Immediate

---

### Strategy 3: Reduce Number of MCP Server Instances

**Description:**
Instead of spawning a new MCP server instance for each VS Code window, implement a shared server architecture where a single MCP server serves multiple clients.

**Approach:**
1. Run MCP servers as standalone HTTP services instead of stdio-based per-window instances
2. Configure VS Code to connect to shared MCP servers via HTTP/SSE transport
3. Use a process manager (systemd, supervisor) to manage long-running MCP servers
4. Implement connection pooling and session management

**Implementation:**
```bash
# Run MCP server as a shared HTTP service
python -m svg_mcp --transport http --port 8080

# Configure VS Code MCP settings to use HTTP transport
# In .vscode/mcp.json or similar:
{
  "servers": {
    "svg-mcp": {
      "transport": "http",
      "url": "http://localhost:8080"
    }
  }
}
```

**Pros:**
- Dramatically reduces number of server instances (from N to 1)
- Reduces total CPU usage proportionally
- Better resource utilization
- Easier to monitor and manage

**Cons:**
- Requires changes to VS Code MCP configuration
- May require authentication/authorization for multi-user scenarios
- Single point of failure (though can be mitigated with process supervision)
- HTTP transport may have different characteristics than stdio

**Effort:** Medium (4-8 hours)
**Impact:** Very High (reduces instances from 14 to 2)
**Timeline:** Immediate

---

### Strategy 4: Patch FastMCP Locally with Idle Detection

**Description:**
Fork or monkey-patch fastmcp to add idle detection that reduces polling frequency when no requests are being processed.

**Approach:**
1. Monitor request activity and track idle time
2. When idle for a threshold period (e.g., 1 second), reduce polling frequency
3. When a request arrives, immediately switch back to normal polling
4. Implement adaptive polling that adjusts based on request patterns

**Implementation:**
```python
import asyncio
import time

class AdaptivePoller:
    def __init__(self, min_interval=0.001, max_interval=0.1, idle_threshold=1.0):
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.idle_threshold = idle_threshold
        self.last_activity = time.time()
        self.current_interval = min_interval

    def on_activity(self):
        self.last_activity = time.time()
        self.current_interval = self.min_interval

    async def wait(self):
        idle_time = time.time() - self.last_activity
        if idle_time > self.idle_threshold:
            self.current_interval = min(
                self.current_interval * 1.5,
                self.max_interval
            )
        await asyncio.sleep(self.current_interval)
```

**Pros:**
- Directly addresses the busy-polling issue
- Can be fine-tuned for specific use cases
- Maintains responsiveness when needed

**Cons:**
- Requires maintaining a fork or complex monkey-patching
- May introduce subtle bugs
- Needs thorough testing
- May break with fastmcp updates

**Effort:** High (8-16 hours)
**Impact:** High
**Timeline:** 1-2 days

---

## Comparison Matrix

| Strategy | Effort | Impact | Timeline | Risk | Maintainability |
|----------|--------|--------|----------|------|-----------------|
| 1. Report Upstream | Low | High | Unknown | Low | High |
| 2. Event Loop Config | Medium | Medium-High | Immediate | Medium | Medium |
| 3. Shared Server | Medium | Very High | Immediate | Low | High |
| 4. Local Patch | High | High | 1-2 days | High | Low |

---

## Recommendation

**Primary Strategy: Strategy 3 (Shared Server Architecture)**

This strategy provides the highest impact with reasonable effort. By reducing the number of MCP server instances from 14 to 2 (one svg-mcp and one imagen-mcp), we can reduce idle CPU usage from ~20% to ~2.6%.

**Secondary Strategy: Strategy 1 (Report Upstream)**

In parallel, we should report the issue to fastmcp maintainers. This ensures the root cause gets fixed for the broader community and we can eventually remove our workarounds.

**Fallback Strategy: Strategy 2 (Event Loop Configuration)**

If the shared server architecture is not feasible for some reason (e.g., VS Code MCP client limitations), we can try configuring the event loop with uvloop or other optimizations.

---

## Next Steps

1. Evaluate VS Code MCP client support for HTTP transport
2. Implement shared server architecture for svg-mcp
3. File issue on fastmcp GitHub repository
4. Monitor upstream for fixes
5. Document the new architecture for users

---

## References

- [FastMCP GitHub Repository](https://github.com/jlowin/fastmcp)
- [MCP SDK Repository](https://github.com/modelcontextprotocol/python-sdk)
- [uvloop - Fast asyncio event loop](https://github.com/MagicStack/uvloop)
- [Original Issue Document](/home/adam/tmp/empty-AI/docs/fastmcp-cpu-usage-issue.md)

---

## Document History

| Date | Author | Description |
|------|--------|-------------|
| 2025-12-25 | AI Assistant | Initial plan created |
