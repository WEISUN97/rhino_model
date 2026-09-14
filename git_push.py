import subprocess
import sys
from pathlib import Path

# ==============================
# Settings
# ==============================

PROJECT_DIR = Path("/Users/bubble/Desktop/Model/Rhino/rhino_model")


# ==============================
# Git
# ==============================


def run_git(args):
    """Run a Git command."""
    result = subprocess.run(["git"] + args, cwd=PROJECT_DIR, text=True)

    if result.returncode != 0:
        print("Git command failed:", "git", *args)
        sys.exit(result.returncode)


def main(message):

    print("Project:", PROJECT_DIR)
    print("Commit:", message)

    # git add
    print("\n[1/3] git add")
    run_git(["add", "-A"])

    # Check whether there are changes to commit
    result = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=PROJECT_DIR)

    if result.returncode == 0:
        print("No changes to commit.")
        return

    # git commit
    print("\n[2/3] git commit")
    run_git(["commit", "-m", message])

    # git push
    print("\n[3/3] git push")
    run_git(["push"])

    print("\nPush completed successfully!")


if __name__ == "__main__":
    main("auto run")
