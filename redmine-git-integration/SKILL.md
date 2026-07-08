---
name: redmine-git-integration
description: Analyzes git commits or branch differences, summarizes the changes, and creates or updates Redmine issues using the redmine MCP server tools. Trigger this skill when the user wants to log git diffs/commits into Redmine.
---

# Redmine Git Integration Skill

This skill guides the agent to analyze git changes (specific commits, branch differences, or tags) and log them into Redmine as new or updated issues.

## Prerequisites
- The `redmine` MCP server must be configured and connected.
- Access to the local git repository.

## Workflow

1. **Prerequisites Verification (MCP Check)**:
   - **CRITICAL**: Before executing any other steps, verify if the required Redmine MCP tools are available in the current session.
   - Check if you can access Redmine tools (e.g., `get_current_user` or `list_redmine_issues`).
   - If the Redmine MCP server is missing or unresponsive, immediately stop the workflow and output a clear error message to the user:
     > **[!] 錯誤：環境設定不足**
     > 本技能需要 `redmine` MCP Server。請確認它已在您的 Antigravity 主程式設定檔（config.json）中配置。
     >
     > **安裝來源網址：**
     > * **Redmine MCP Server**: https://github.com/jztan/redmine-mcp-server
   - If verification passes, proceed to Step 2.

2. **Parameters Verification**:
   - Ask the user for the Git reference (e.g. commit hashes, `main..feature`, or tag names).
   - Ask if they want to **Create a new issue** or **Update an existing issue**.
   - Get the Redmine Project ID (for new issues) or Issue ID (for updates).

3. **Git Diff & Analysis**:
   - Execute git commands or helper scripts (e.g. `scripts/git_diff_analyzer.py`) to retrieve:
     - The commit messages in the specified range.
     - The files changed.
     - The actual code differences (`git diff`) if needed for deeper context.
   - Summarize the modifications:
     - **Goal/Purpose**: What problem does this change solve?
     - **Key Changes**: Bullet points explaining what files/modules were changed and why.
     - **Impact**: Any potential risks or side effects.

4. **Redmine Issue Processing**:
  - **Case A: Create New Issue**:
     - Call `create_redmine_issue` with:
       - `project_id`: Project identifier.
       - `subject`: Concise summary of the changes.
       - `description`: The detailed summary of the modifications generated in Step 3.
   - **Case B: Update Existing Issue**:
     - Retrieve current status using `get_redmine_issue`.
     - Call `update_redmine_issue` to add a note/journal entry with the summarized git changes.
     - (Optional) Prompt the user if they want to change the status (e.g., to "Resolved" or "In Review").
   - **Case C: Code Logic Verification & Implementation Concept**:
     - Call `get_redmine_issue` using the Redmine Issue ID to fetch the detailed requirements.
     - Analyze the git diff or specified files against the fetched requirements.
     - Formulate an evaluation report containing:
       - **Requirements Coverage**: Detailed check of whether the current code logic satisfies each requirement of the issue.
       - **Implementation Concept (實作概念)**: Clear description of the technical design, architectural patterns, algorithms, or API designs used in the code.
       - **Remaining Gaps / Risks**: Any missing parts or potential edge case vulnerabilities.
     - Call `update_redmine_issue` to post this evaluation report as a new note (journal entry) on the issue.

## Guidelines for the Agent
- Be structured in the summaries: separate user-facing changes from internal refactoring.
- Keep the Redmine description/notes formatted in standard Redmine textile or markdown format.
- For Case C, be objective when judging whether requirements are met, highlighting code files and lines where possible.
- Always confirm the summary text with the user before invoking the Redmine MCP tools.
