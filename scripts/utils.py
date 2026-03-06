import os

def generate_account_id(base_path="../outputs/accounts"):

    os.makedirs(base_path, exist_ok=True)

    existing = [
        d for d in os.listdir(base_path)
        if d.startswith("account_")
    ]

    numbers = []

    for acc in existing:
        try:
            numbers.append(int(acc.split("_")[1]))
        except:
            pass

    next_id = max(numbers) + 1 if numbers else 1

    return f"account_{next_id:03d}"