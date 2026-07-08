#!/usr/bin/env python3
import subprocess
import sys
import argparse

def get_git_log(git_range):
    """
    Get git commit logs in the specified range.
    """
    try:
        cmd = ['git', 'log', git_range, '--oneline', '--no-merges']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running git log: {e.stderr}", file=sys.stderr)
        return None

def get_git_diff_stat(git_range):
    """
    Get git diff stat to see which files were changed.
    """
    try:
        cmd = ['git', 'diff', '--stat', git_range]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running git diff: {e.stderr}", file=sys.stderr)
        return None

def main():
    parser = argparse.ArgumentParser(description="Analyze Git differences between commits/branches.")
    parser.add_argument("range", help="Git range (e.g., commit1..commit2, branch-a..branch-b, or commit_hash)")
    args = parser.parse_args()

    print(f"=== Analyzing Git Range: {args.range} ===\n")
    
    print("--- Commit History ---")
    log = get_git_log(args.range)
    if log:
        print(log)
    else:
        print("No commits found or invalid range.")
    
    print("\n--- File Changes Stat ---")
    stat = get_git_diff_stat(args.range)
    if stat:
        print(stat)
    else:
        print("No files changed or invalid range.")

if __name__ == "__main__":
    main()
