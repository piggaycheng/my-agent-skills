---
name: weekly-report-generator-google-slides
description: Automatically fetches Redmine issues updated/created in the current week, retrieves progress from issue notes, filters out issues with subtasks to only include leaf-node tasks, copies the official "盟立集團-新版ppt-2" Google Slides template, renames it to <使用者名稱>_週報_<這周週五的年月日>, and populates the weekly report using the google-workspace MCP server.
---

# Weekly Report Generator Skill (Google Slides & Redmine)

This skill guides the agent in gathering Redmine issues for the current week, extracting status updates and details from their note journals, filtering for leaf-node tasks (issues with no subtasks), copying Mirle Group's official Google Slides template (`盟立集團-新版ppt-2`), renaming the copy to `<使用者名稱>_週報_<這周週五的年月日>`, and generating a professional weekly report slide deck directly in Google Slides using the `google-workspace` MCP server.

## Prerequisites
- The **Redmine** MCP server must be configured and running.
- The **Google Workspace** MCP server (`google-workspace`) must be configured and authenticated.
- The official Mirle Group template presentation named `盟立集團-新版ppt-2` must exist on Google Drive.
- The `uv` command-line tool must be installed on the system to execute Python scripts with dependencies.

## Workflow

1. **Prerequisites Verification (MCP Check)**:
   - **CRITICAL**: Before executing any other steps, verify if the required MCP tools are available in the current environment.
   - Check if you can access Redmine tools (e.g., `get_current_user` or `list_redmine_issues`) and Google Workspace tools (e.g., `copy_drive_file`, `search_drive_files`, or `batch_update_presentation`).
   - If either MCP server is missing or unresponsive, immediately stop the workflow and output a clear error message to the user:
     > **[!] 錯誤：環境設定不足**
     > 本技能需要 `redmine` 與 `google-workspace` 兩個 MCP Server。請確認它們已在您的 Antigravity 主程式設定檔（config.json）中配置。
   - Verify that the template file `盟立集團-新版ppt-2` is searchable on Google Drive via `search_drive_files`.
   - If verification passes, proceed to Step 2.

2. **Calculate Date Window & Friday Date**:
   - Determine the start date (Monday) and end date (Sunday) of the current week.
   - Calculate the date of Friday in the current week (Monday + 4 days) and format it as `YYYYMMDD` (e.g. `20260724`).
   - For example, if today is `2026-07-23` (Thursday), Monday is `2026-07-20`, Sunday is `2026-07-26`, and Friday is `20260724`.

3. **Retrieve User Name & Issues from Redmine**:
   - Retrieve current user details using `get_current_user` to obtain `<使用者名稱>` (e.g., `王小明` or `xiaoming`).
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
       "user_name": "使用者名稱",
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

8. **Copy Template & Generate Google Slides Presentation**:
   - Run the Python Google Slides generator script using `uv`:
     `uv run --with google-api-python-client --with google-auth scripts/generate_weekly_report_gslides.py <scratch/issues.json> [user_google_email] [user_name]`
   - The script will automatically:
     - Search Google Drive for the template presentation named `盟立集團-新版ppt-2`.
     - Copy the template file to create a new Google Slides presentation named `<使用者名稱>_週報_<這周週五的年月日>` (e.g. `王小明_週報_20260724`).
     - Set the **title of Slide 1** to match the file name: `<使用者名稱>_週報_<這周週五的年月日>`.
     - Update Slide 1 subtitle with the date range (`start_date ~ end_date`), report generation date, and reporter name.
     - Generate slide(s) containing a structured, formatted table of issues and their statuses (paginated in chunks of 10 if there are many issues).
     - Generate one detail slide per issue with a left column card containing metadata (project, status, assignee, creation date) and a right column containing bulleted progress updates.
     - Output the created Presentation ID and direct link to the Google Slides deck.

9. **Aesthetic Quality Control**:
   - Call `get_page` or `get_page_thumbnail` from the `google-workspace` MCP server to inspect the generated slides.
   - Verify alignment, contrast, readability, and ensure no text overflows or overlaps.
