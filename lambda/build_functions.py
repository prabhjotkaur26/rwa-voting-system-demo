import os
import zipfile

FUNCTIONS = [
    "send_otp",
    "verify_otp",
    "cast_vote",
    "get_results",
    "create_election",
    "add_candidates"
]

BASE_DIR = os.path.dirname(__file__)
BUILD_DIR = os.path.join(BASE_DIR, ".build")

os.makedirs(BUILD_DIR, exist_ok=True)

for fn in FUNCTIONS:
    fn_dir = os.path.join(BASE_DIR, fn)
    zip_path = os.path.join(BUILD_DIR, f"{fn}.zip")

    with zipfile.ZipFile(zip_path, 'w') as z:
        for root, dirs, files in os.walk(fn_dir):
            for file in files:
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, fn_dir)
                z.write(filepath, arcname)

    print(f"Built {zip_path}")
