# This script runs the full pipeline automatically

import subprocess
import os
import sys

from utils import generate_account_id


# -----------------------
# Handle transcript input
# -----------------------

if len(sys.argv) > 1:
    transcript_file = sys.argv[1]
else:
    # default for manual testing
    transcript_file = "demo_call_1.txt"


# -----------------------
# Script directory
# -----------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# -----------------------
# Helper to run scripts
# -----------------------

def run_script(script_name, args=None):

    cmd = ["python", script_name]

    if args:
        cmd.extend(args)

    print(f"\nRunning {' '.join(cmd)}...")

    try:

        subprocess.run(
            cmd,
            cwd=SCRIPT_DIR,
            check=True
        )

    except subprocess.CalledProcessError as e:

        print(f"\nError while running {script_name}")
        print(e)

        sys.exit(1)


# -----------------------
# Main pipeline
# -----------------------

def main():

    # Generate new account id
    account_id = generate_account_id()

    print(f"\nUsing account: {account_id}")

    transcript_path = f"../transcripts/{transcript_file}"
    memo_path = f"../outputs/accounts/{account_id}/v1/memo.json"

    # Step 1 — Regex extraction
    run_script(
        "save_memo.py",
        [account_id, transcript_path]
    )

    # Step 2 — LLM validation
    run_script(
        "validate_with_llm.py",
        [memo_path, transcript_path]
    )

    # Step 3 — Generate agent
    run_script(
        "generate_agent.py",
        [account_id]
    )

    # Step 4 — Version update
    run_script(
        "version_update.py",
        [account_id]
    )

    # Step 5 — Diff generation
    run_script(
        "generate_diff.py",
        [account_id]
    )

    print("\nPipeline completed successfully.")


# -----------------------

if __name__ == "__main__":
    main()