# This script updates the memo from onboarding data and creates v2

import json
import os
from extract_memo import extract_information


V1_MEMO = "../outputs/accounts/account_001/v1/memo.json"
ONBOARDING_FILE = "../onboarding/onboarding_1.txt"
V2_FOLDER = "../outputs/accounts/account_001/v2"


def main():

    # load old memo
    with open(V1_MEMO, "r", encoding="utf-8") as f:
        old_memo = json.load(f)

    # read onboarding transcript
    with open(ONBOARDING_FILE, "r", encoding="utf-8") as f:
        onboarding_text = f.read()

    # extract new info
    new_data = extract_information(onboarding_text)

    updated_memo = old_memo.copy()

    # update fields if new data exists
    for key in new_data:
        if new_data[key] not in [None, [], ""]:
            updated_memo[key] = new_data[key]

    os.makedirs(V2_FOLDER, exist_ok=True)

    v2_path = os.path.join(V2_FOLDER, "memo.json")

    with open(v2_path, "w", encoding="utf-8") as f:
        json.dump(updated_memo, f, indent=4)

    print("\nVersion 2 memo created.")
    print("Saved at:", v2_path)


if __name__ == "__main__":
    main()