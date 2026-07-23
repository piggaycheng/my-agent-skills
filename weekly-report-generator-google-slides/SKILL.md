---
name: weekly-report-generator-google-slides
description: Automatically fetches Redmine issues updated/created in the current week, retrieves progress from issue notes, filters out issues with subtasks to only include leaf-node tasks, and compiles them into a Google Slides presentation using the google-workspace MCP server.
---

# Weekly Report Generator Skill (Google Slides & Redmine)

This skill guides the agent in gathering Redmine issues for the current week, extracting status updates and details from their note journals, filtering for leaf-node tasks (issues with no subtasks), and generating a professional weekly report slide deck directly in Google Slides using the `google-workspace` MCP server.

## Prerequisites
- The **Redmine** MCP server must be configured and running.
- The **Google Workspace** MCP server (`google-workspace`) must be configured and authenticated.
- The `uv` command-line tool must be installed on the system to execute Python scripts with dependencies.

## Workflow

1. **Prerequisites Verification (MCP Check)**:
   - **CRITICAL**: Before executing any other steps, verify if the required MCP tools are available in the current environment.
   - Check if you can access Redmine tools (e.g., `get_current_user` or `list_redmine_issues`) and Google Workspace tools (e.g., `create_presentation` or `batch_update_presentation`).
   - If either MCP server is missing or unresponsive, immediately stop the workflow and output a clear error message to the user:
     > **[!] 錯誤：環境設定不足**
     > 本技能需要 `redmine` 與 `google-workspace` 兩個 MCP Server。請確認它們已在您的 Antigravity 主程式設定檔（config.json）中配置。
   - If verification passes, proceed to Step 2.

2. **Calculate Date Window**:
   - Determine the start date of the current week (Monday) and the end date (Sunday).
   - For example, if today is `2026-07-08` (Wednesday), the start date (Monday) is `2026-07-06`.

3. **Retrieve Issues from Redmine**:
   - Call `list_redmine_issues` with the following parameters:
     - `status_id`: `"*"` (retrieve all statuses)
     - `assigned_to_id`: `"me"` (retrieve issues assigned to the current user)
     - `filters`: `{"created_on": ">=YYYY-MM-DD"}` (using Monday's date)
     - `sort`: `"updated_on:desc"`
     - `limit`: `100`

4. **Identify Leaf Nodes (Batch Query)**:
   - Collect the IDs of all candidate issues retrieved in Step 3.
   - Perform a batch query using `list_redmine_issues` to find all subtasks whose `parent_id` is in the candidate IDs list.
   - Extract the `parent.id` from the returned subtasks. Any candidate ID that appears as a parent is a parent task (not a leaf node) and should be discarded.
   - The remaining candidate issues that do not have any subtasks in Redmine are our leaf-node issues.

5. **Fetch Progress Notes & Details (Leaf Nodes Only)**:
   - For each identified leaf-node issue:
     - Call `get_redmine_issue` with `issue_id` and `include_journals=True` to retrieve its description and note journals.

6. **Summarize Progress**:
   - Use the LLM to analyze the description and note journals for each leaf issue (focusing on the latest comments from the assignee).
   - Extract 3-5 concise, professional, action-oriented bullet points summarizing:
     - What was achieved/completed.
     - Current implementation details or logic.
     - Next steps or blockers (if any).

7. **Generate Issues JSON**:
   - Save the consolidated leaf-node issue data into a temporary JSON file at `scratch/issues.json` in the conversation's scratch directory:
     `<appDataDir>/brain/<conversation-id>/scratch/issues.json`
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

8. **Generate Google Slides Presentation**:
   - Run the Python Google Slides generator script using `uv`:
     `uv run --with google-api-python-client --with google-auth scripts/generate_weekly_report_gslides.py <scratch/issues.json> [user_google_email]`
   - The script will automatically:
     - Connect to Google Slides API using credentials managed by `google-workspace` MCP.
     - Create a new presentation titled "盟立集團 工作週報 (YYYY-MM-DD ~ YYYY-MM-DD)".
     - Create Slide 1 as the Title slide with a dark blue theme (`#1A365D`), displaying the title, date range, creation time, and team name.
     - Generate slide(s) containing a structured, formatted table of issues and their statuses (paginated in chunks of 10 if there are many issues).
     - Generate one detail slide per issue with a left column card containing metadata (project, status, assignee, creation date) and a right column containing bulleted progress updates.
     - Output the created Presentation ID and direct link to the Google Slides deck.

9. **Aesthetic Quality Control**:
   - Call `get_page` or `get_page_thumbnail` from the `google-workspace` MCP server to inspect the generated slides.
   - Verify alignment, contrast, readability, and ensure no text overflows or overlaps.
