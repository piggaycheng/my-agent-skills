#!/usr/bin/env python3
import subprocess
import sys
from datetime import datetime, timedelta

def get_git_commits(days=7):
    """
    Get git commits from the last N days.
    """
    since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    try:
        cmd = [
            'git', 'log', 
            f'--since={since_date}', 
            '--oneline', 
            '--no-merges'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e}", file=sys.stderr)
        return None
    except FileNotFoundError:
        print("Git executable not found in PATH.", file=sys.stderr)
        return None

def main():
    print("--- Fetching Git Commits from the past 7 days ---")
    commits = get_git_commits(7)
    if commits:
        print(commits)
    else:
        print("No commits found or error occurred.")

if __name__ == "__main__":
    main()
