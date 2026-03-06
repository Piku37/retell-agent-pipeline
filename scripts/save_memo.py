# This script extracts information and saves it as memo.json

import json
import os
import sys

from extract_memo import extract_information


# -----------------------
# Read arguments
# -----------------------

if len(sys.argv) < 3:
    print("Usage: python save_memo.py <account_id> <transcript_path>")
    sys.exit(1)

account_id = sys.argv[1]
transcript_path = sys.argv[2]


# -----------------------
# Output folder
# -----------------------

OUTPUT_FOLDER = f"../outputs/accounts/{account_id}/v1"


def main():

    # read transcript
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    # extract information
    memo = extract_information(transcript)

    # ensure output folder exists
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # save json
    output_path = os.path.join(OUTPUT_FOLDER, "memo.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(memo, f, indent=4)

    print("\nMemo saved successfully at:")
    print(output_path)


if __name__ == "__main__":
    main()