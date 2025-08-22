# Testing Notes

## Known Issues

### OpenAI Agents SDK Shutdown Logging

The OpenAI Agents SDK has a known issue where it tries to log during Python shutdown after pytest has closed logging streams. This results in harmless "I/O operation on closed file" errors at the end of test runs.

**This is cosmetic only** - it doesn't affect test results or functionality.

**Root cause:** SDK registers `atexit.register(get_trace_provider().shutdown)` which tries to log during shutdown.

**Status:** Tests work perfectly, just ignore the shutdown errors at the end.

## Test Coverage Status

**Current: 55% with 328 passing tests**

### Excellent Coverage (AI-Safe)

- **Config: 90%** - Real settings validation
- **Utils/logging: 60%** - Real logging functionality
- **Agent monitoring: 86%** - Real performance monitoring
- **Agent tools: 85-96%** - Real GitHub integration
- **Security monitor: 78%** - Real security validation

### Quality Focus

All tests focus on **real functionality** rather than placeholder code:

- ✅ **Real business logic** tested
- ✅ **Actual error handling** validated
- ✅ **True integration** verified
- ✅ **Edge cases** caught

## Coverage Philosophy

**Quality over Quantity:** 55% coverage of real, meaningful functionality is better than 80% coverage that includes placeholder code and stub implementations.

**AI Safety Focus:** Tests validate that AI agents can't break core functionality when they modify code.
