# Example Usage: Redmine Git Integration

Below is an example of how the Agent applies this skill to process a user's request.

## User Request
> "Help me review the differences between `main` and `feature/login-ui`, summarize the purpose, and update Redmine issue #1234."

## Agent Execution Flow

1. **Analysis Step**:
   The agent runs:
   ```bash
   python scripts/git_diff_analyzer.py main..feature/login-ui
   ```

   **Output received**:
   ```text
   === Analyzing Git Range: main..feature/login-ui ===

   --- Commit History ---
   a1b2c3d Refactored login page design and added validation
   e5f6g7h Added Google OAuth integration for client login
   i9j0k1l Initial layout for custom login UI styling

   --- File Changes Stat ---
   src/components/Login.js       | 45 ++++++++++++++++++++++++++-
   src/styles/login.css          | 68 +++++++++++++++++++++++++++++++++++++++++++
   package.json                  |  2 +
   3 files changed, 114 insertions(+), 1 deletion(-)
   ```

2. **Summarization**:
   The agent creates a summary description of these changes:
   > **Summary of changes (main..feature/login-ui)**:
   > * **Objective**: Implement a modern, responsive login interface with social login validation.
   > * **Key Modifications**:
   >   * Developed login form styling in `login.css` with glassmorphism aesthetics.
   >   * Integrated Google OAuth library in `Login.js` and updated dependencies in `package.json`.
   >   * Added client-side email/password validation check.

3. **User Confirmation**:
   The agent asks:
   > "I've compiled the change summary. Would you like me to add this as a note to Redmine Issue #1234 now?"

4. **Redmine Update**:
   Upon confirmation, the agent triggers:
   * **MCP tool**: `update_redmine_issue`
   * **Arguments**:
     ```json
     {
       "issue_id": 1234,
       "notes": "### Git Changes Summary (main..feature/login-ui)\n\n* **Objective**: Implement a modern, responsive login interface with social login validation.\n* **Key Modifications**:\n  * Developed login form styling in `login.css` with glassmorphism aesthetics.\n  * Integrated Google OAuth library in `Login.js` and updated dependencies in `package.json`.\n  * Added client-side email/password validation check."
     }
     ```

---

## Example 2: Code Verification & Implementation Concept Logging (Case C)

## User Request
> "Verify if my current commits in `feature/api-cache` meet the requirements of Redmine Issue #5678, and log the verification & implementation concept into the issue notes."

## Agent Execution Flow

1. **Fetch Issue Details**:
   The agent calls `get_redmine_issue` with ID `5678`.
   **Requirement Details retrieved**:
   > **Issue #5678: Implement API response caching**
   > * **Requirement 1**: Cache user configuration API calls for 10 minutes.
   > * **Requirement 2**: Provide a header `X-Cache-Status` showing `HIT` or `MISS`.
   > * **Requirement 3**: Implement a manual cache-invalidation mechanism.

2. **Analysis Step**:
   The agent runs `python scripts/git_diff_analyzer.py main..feature/api-cache` and reviews the code diff of the changes.

3. **Evaluation**:
   The agent compares the code changes with the requirements:
   * **Req 1 (10-min cache)**: Satisfied. Code in `services/cache.js` uses standard Redis TTL set to 600 seconds.
   * **Req 2 (Header)**: Satisfied. Express middleware in `routes/config.js` sets the `X-Cache-Status` header appropriately.
   * **Req 3 (Invalidation)**: **Partial / Gap**. Invalidation endpoint `/api/config/clear-cache` is defined, but it lacks authentication, which poses a security risk.

4. **Formulate Report (with Implementation Concept / 實作概念)**:
   The agent formats the following analysis:
   > ### 🛡️ Requirements Verification & Implementation Concept
   > 
   > **1. Implementation Concept (實作概念)**
   > - **Caching Layer**: Configured a Redis-backed caching middleware intercepting requests on `/api/user/config`.
   > - **Header injection**: The middleware inspects the cache query result; if found, it responds with cache data and headers `X-Cache-Status: HIT`. Otherwise, it queries the DB, stores the result with a 600s TTL, and returns `X-Cache-Status: MISS`.
   > - **Invalidation Endpoint**: Exposed a POST route `/api/config/clear-cache` to flush Redis cache keys.
   > 
   > **2. Requirements Coverage Status**
   > - [x] **Requirement 1 (10-min Cache)**: Met (Implemented Redis TTL = 600s).
   > - [x] **Requirement 2 (Cache Status Header)**: Met (Added `X-Cache-Status` response header).
   > - [!] **Requirement 3 (Manual Invalidation)**: **Warning / Incomplete**. The endpoint `/api/config/clear-cache` is accessible but does not verify user roles. Recommend adding auth middleware before closing the issue.

5. **Redmine Update**:
   Upon user confirmation, the agent updates the issue:
   * **MCP tool**: `update_redmine_issue`
   * **Arguments**:
     ```json
     {
       "issue_id": 5678,
       "notes": "### 🛡️ Requirements Verification & Implementation Concept\n\n**1. Implementation Concept (實作概念)**\n- **Caching Layer**: Configured a Redis-backed caching middleware intercepting requests on `/api/user/config`.\n- **Header injection**: The middleware inspects the cache query result; if found, it responds with cache data and headers `X-Cache-Status: HIT`. Otherwise, it queries the DB, stores the result with a 600s TTL, and returns `X-Cache-Status: MISS`.\n- **Invalidation Endpoint**: Exposed a POST route `/api/config/clear-cache` to flush Redis cache keys.\n\n**2. Requirements Coverage Status**\n- [x] **Requirement 1 (10-min Cache)**: Met (Implemented Redis TTL = 600s).\n- [x] **Requirement 2 (Cache Status Header)**: Met (Added `X-Cache-Status` response header).\n- [!] **Requirement 3 (Manual Invalidation)**: **Warning / Incomplete**. The endpoint `/api/config/clear-cache` is accessible but does not verify user roles. Recommend adding auth middleware before closing the issue."
     }
     ```

