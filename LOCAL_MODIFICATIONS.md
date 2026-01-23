# Local Modifications

This is a fork of [google_workspace_mcp](https://github.com/taylorwilsdon/google_workspace_mcp) with local modifications.

## OAuth State Persistence Fix (2026-01-23)

**Problem:** OAuth authentication failed with "Invalid or expired OAuth state parameter" after completing Google authorization.

**Root Cause:** OAuth states were stored only in memory (`self._oauth_states: Dict`). When the MCP process ended between starting the OAuth flow and receiving the callback, the state was lost.

**Fix:** OAuth states are now persisted to `~/.google_workspace_mcp/oauth_states.json`.

**Modified File:** `auth/oauth21_session_store.py`

**Changes:**
- Added `_get_state_file_path()` - returns path to persisted states file
- Added `_load_persisted_states()` - loads states from JSON file with datetime parsing
- Added `_save_persisted_states()` - saves states to JSON file with datetime serialization
- Modified `store_oauth_state()` to persist states after storing
- Modified `validate_and_consume_oauth_state()` to load persisted states before validating

**Remaining Limitation:** The OAuth callback server runs as a daemon thread and dies when the MCP process ends. If the process terminates while waiting for the OAuth callback, the callback URL won't be reachable.

**Workaround:** If the callback fails, copy the full callback URL from the browser and provide it manually. The server can then extract the authorization code and complete the token exchange.

**Commit:** `9ff4ef5 Fix OAuth state persistence across process restarts`
