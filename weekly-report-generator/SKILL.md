---
name: weekly-report-generator
description: Handles generating structured weekly status reports by analyzing git commits, tasks, and using templates. Trigger this skill when the user asks to generate, update, or edit a weekly report.
---

# Weekly Report Generator Skill

This skill guides the agent in gathering, formatting, and presenting weekly progress reports for the user.

## Workflow

1. **Information Gathering**:
   - Collect recent git commits (e.g., using `git log --since="7 days ago" --oneline`).
   - Query project tasks or ticket updates if applicable.
   - Read the user's input/notes for additional context.

2. **Template Application**:
   - Load the weekly report template from `resources/report_template.md`.
   - Fill out the template sections:
     - **Overview / Summary**: A high-level 2-3 sentence summary of the week's focus.
     - **Key Achievements**: Bulleted list of completed work.
     - **In Progress / Current Focus**: What is currently being worked on.
     - **Next Steps / Upcoming Tasks**: Plans for the next week.
     - **Blockers / Risks**: Any issues preventing progress.

3. **Refinement**:
   - Present the drafted report to the user as an artifact or direct message.
   - Ask for confirmation or edits.

## Guidelines for the Agent
- Keep descriptions clear, action-oriented, and concise.
- Group commits by feature or topic rather than listing every raw commit message.
- Use professional and clear language.
- Link to relevant issue tracker tickets if they are provided.
