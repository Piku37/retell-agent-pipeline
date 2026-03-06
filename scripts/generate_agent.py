# This script generates an AI agent specification from the account memo

import json
import os

MEMO_PATH = "../outputs/accounts/account_001/v1/memo.json"
TEMPLATE_PATH = "../templates/agent_prompt.txt"
OUTPUT_PATH = "../outputs/accounts/account_001/v1/agent_spec.json"


def main():

    # load memo
    with open(MEMO_PATH, "r", encoding="utf-8") as f:
        memo = json.load(f)

    # load template
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    # prepare replacements
    services = ", ".join(memo["services_supported"])

    prompt = template.replace("{{company_name}}", str(memo["company_name"]))
    prompt = prompt.replace("{{business_hours}}", str(memo["business_hours"]))
    prompt = prompt.replace("{{services}}", services)
    prompt = prompt.replace("{{emergency_definition}}", str(memo["emergency_definition"]))

    agent_spec = {
        "agent_name": f"{memo['company_name']} Assistant",
        "voice_style": "friendly professional",
        "system_prompt": prompt,
        "version": "v1"
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(agent_spec, f, indent=4)

    print("\nAgent spec created successfully.")
    print("Saved at:", OUTPUT_PATH)


if __name__ == "__main__":
    main()