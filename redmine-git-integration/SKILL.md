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

1. **Parameters Verification**:
   - Ask the user for the Git reference (e.g. commit hashes, `main..feature`, or tag names).
   - Ask if they want to **Create a new issue** or **Update an existing issue**.
   - Get the Redmine Project ID (for new issues) or Issue ID (for updates).

2. **Git Diff & Analysis**:
   - Execute git commands or helper scripts (e.g. `scripts/git_diff_analyzer.py`) to retrieve:
     - The commit messages in the specified range.
     - The files changed.
     - The actual code differences (`git diff`) if needed for deeper context.
   - Summarize the modifications:
     - **Goal/Purpose**: What problem does this change solve?
     - **Key Changes**: Bullet points explaining what files/modules were changed and why.
     - **Impact**: Any potential risks or side effects.

3. **Redmine Issue Processing**:
  - **Case A: Create New Issue**:
     - Call `create_redmine_issue` with:
       - `project_id`: Project identifier.
       - `subject`: Concise summary of the changes.
       - `description`: The detailed summary of the modifications generated in Step 2.
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

