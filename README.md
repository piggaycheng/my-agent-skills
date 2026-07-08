# Antigravity Developer Skills Collection

This repository contains a collection of custom Agent Skills for Google Antigravity to automate developer workflows.

## 📦 Available Skills

| Skill Folder | Description | Trigger Example |
| :--- | :--- | :--- |
| **`weekly-report-generator`** | Automatically fetches Redmine issues assigned to the user for the current week, filters out parent tasks (keeping leaf nodes), summarizes progress notes, and generates a PowerPoint report using Mirle Group's official template. | *"取得我這週的 Redmine issue 並用盟立公版產生週報 PPT"* |
| **`redmine-git-integration`** | Analyzes git diffs/commits and logs them directly to Redmine issues. | *"Analyze the commits between main and dev, then update Redmine issue #1234"* |

---

## 🛠️ Installation

You can install this skill collection either for a **specific project workspace** (recommended for teams) or **globally** (for personal use across all projects).

### 🏠 Option 1: Workspace-Specific Installation
Clone this entire repository into your project's `.agents/skills/` directory:

```bash
# 1. Navigate to your project's root directory
cd /path/to/your/project

# 2. Clone the repository into the .agents/skills directory
git clone https://github.com/your-username/antigravity-skills-collection.git .agents/skills/my-skills
```

*Note: Once cloned, the Antigravity agent will recursively scan all subfolders and load both skills automatically.*

---

### 🌍 Option 2: Global Installation
To make these skills available to your Antigravity agent in **any** workspace, clone it into your global Antigravity config directory:

#### On Windows (PowerShell):
```powershell
git clone https://github.com/your-username/antigravity-skills-collection.git "$HOME\.gemini\config\skills\my-skills"
```

#### On macOS / Linux:
```bash
git clone https://github.com/your-username/antigravity-skills-collection.git ~/.gemini/config/skills/my-skills
```

---

## 🚀 How to Use

Once installed, there is **no need for manual loading**. The next time you start a chat with your Antigravity agent:

1. The agent scans the skill paths and loads the metadata from each `SKILL.md`.
2. Based on your prompt, the agent automatically matches and activates the corresponding skill.

---

## 📁 Repository Structure

```text
.
├── README.md                      # This installation guide
├── weekly-report-generator/       # Weekly Report Generator Skill
│   ├── SKILL.md                   # Skill instructions & leaf-node task filter details
│   ├── scripts/
│   │   └── generate_weekly_report.py  # Python PowerPoint COM automation script (runs via uv)
│   └── examples/
│       └── example_issues.json    # Example input data format for PowerPoint generation
└── redmine-git-integration/       # Redmine Git Integration Skill
    ├── SKILL.md
    ├── scripts/
    │   └── git_diff_analyzer.py
    └── examples/
        └── example_usage.md
```
