---
name: weekly-report-generator
description: Automatically fetches Redmine issues updated/created in the current week, retrieves progress from issue notes, filters out issues with subtasks to only include leaf-node tasks, and compiles them into a PowerPoint presentation using the powerpoint MCP server and Mirle Group's official template.
---

# Weekly Report Generator Skill (PowerPoint & Redmine)

This skill guides the agent in gathering Redmine issues for the current week, extracting status updates and details from their note journals, filtering for leaf-node tasks (issues with no subtasks), and generating a professional weekly report slide deck using Mirle Group's official PowerPoint template.

## Prerequisites
- The **Redmine** MCP server must be configured and running.
- The **PowerPoint** MCP server must be running, and the PowerPoint application should be open.
- The official Mirle Group template file must be available at:
  `C:\Users\yucheng\Documents\自訂 Office 範本\盟立集團-新版ppt-2.potx`
- The `uv` command-line tool must be installed on the system to execute Python scripts with dependencies.

## Workflow

1. **Prerequisites Verification (MCP Check)**:
   - **CRITICAL**: Before executing any other steps, verify if the required MCP tools are available in the current environment.
   - Check if you can access Redmine tools (e.g., `get_current_user` or `list_redmine_issues`) and PowerPoint tools (e.g., `ppt_get_app_info` or `ppt_connect`).
   - If either MCP server is missing or unresponsive, immediately stop the workflow and output a clear error message to the user:
     > **[!] 錯誤：環境設定不足**
     > 本技能需要 `redmine` 與 `powerpoint` 兩個 MCP Server。請確認它們已在您的 Antigravity 主程式設定檔（config.json）中配置。
     >
     > **安裝來源網址：**
     > 1. **Redmine MCP Server**: https://github.com/jztan/redmine-mcp-server
     > 2. **PowerPoint MCP Server**: https://github.com/ykuwai/ppt-mcp
   - If verification passes, proceed to Step 2.

2. **Calculate Date Window**:
   - Determine the start date of the current week (Monday) and the end date (Sunday).
   - For example, if today is `2026-07-08` (Wednesday), the start date (Monday) is `2026-07-06`.

3. **Retrieve Issues from Redmine**:
   - Call `list_redmine_issues` with the following parameters:
     - `status_id`: `"*"` (retrieve all statuses)
     - `filters`: `{"created_on": ">=YYYY-MM-DD"}` (using Monday's date)
     - `sort`: `"updated_on:desc"`
     - `limit`: `100`

4. **Fetch Issue Notes & Details (Leaf Nodes Only)**:
   - For each issue retrieved:
     - Call `get_redmine_issue` with `issue_id` to retrieve details, journals, and children (`include_journals=True`, `include_children=True`).
     - **Leaf Node Check**: Inspect the `"children"` field of the issue. If the issue has child tasks (i.e., the `"children"` list is not empty), **discard it**. We only include leaf-node issues that do not contain subtasks.
     - Extract notes and descriptions for the remaining leaf issues.

5. **Summarize Progress**:
   - Use the LLM to analyze the description and note journals for each leaf issue (focusing on the latest comments from the assignee).
   - Extract 3-5 concise, professional, action-oriented bullet points summarizing:
     - What was achieved/completed.
     - Current implementation details or logic.
     - Next steps or blockers (if any).

6. **Generate Issues JSON**:
   - Save the consolidated leaf-node issue data into a temporary JSON file at `scratch/issues.json` in the conversation's scratch directory:
     `C:\Users\yucheng\.gemini\antigravity-cli\brain\<conversation-id>\scratch\issues.json`
   - The JSON schema should look like:
     ```json
     {
       "start_date": "YYYY-MM-DD",
       "end_date": "YYYY-MM-DD",
       "issues": [
         {
           "id": 12345,
           "tracker": "Task",
           "subject": "Leaf Issue Subject",
           "status": "Resolved",
           "assignee": "Assignee Name",
           "project": "Project Name",
           "created_on": "YYYY-MM-DD",
           "key_points": [
             "Summarized progress point 1",
             "Summarized progress point 2"
           ]
         }
       ]
     }
     ```

7. **Generate PowerPoint Presentation**:
   - Run the Python PPTX generator script using `uv`:
     `uv run scripts/generate_weekly_report.py C:\Users\yucheng\.gemini\antigravity-cli\brain\<conversation-id>\scratch\issues.json`
   - The script will automatically:
     - Connect to the running PowerPoint instance and target the active presentation or create a new one using the Mirle template.
     - Keep Slide 1 as the Title slide, updating the title to "盟立集團 工作週報" and the subtitle with the date range.
     - Generate slide(s) containing a structured, formatted table of issues and their statuses (paginated in chunks of 10 if there are many issues).
     - Generate one detail slide per issue using the template's standard content layout, putting metadata in a clean left column card and bulleted progress updates in the right column.

8. **Aesthetic Quality Control**:
   - Call `ppt_get_slide_preview` to inspect the generated slides.
   - Verify alignment, contrast, readability, and ensure no text overflows or overlaps.
