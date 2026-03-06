# This script compares v1 and v2 memos and generates a changes.json file

import json
import os

V1_PATH = "../outputs/accounts/account_001/v1/memo.json"
V2_PATH = "../outputs/accounts/account_001/v2/memo.json"
OUTPUT_PATH = "../outputs/accounts/account_001/changes.json"


def main():

    with open(V1_PATH, "r", encoding="utf-8") as f:
        v1 = json.load(f)

    with open(V2_PATH, "r", encoding="utf-8") as f:
        v2 = json.load(f)

    changes = {}

    for key in v1:
        if v1[key] != v2.get(key):
            changes[key] = {
                "old": v1[key],
                "new": v2.get(key)
            }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(changes, f, indent=4)

    print("\nChange log generated.")
    print("Saved at:", OUTPUT_PATH)


if __name__ == "__main__":
    main()