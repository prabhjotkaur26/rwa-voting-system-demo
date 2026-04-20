import os
import zipfile

# Root lambda folder (jahan yeh script hai)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Build output folder
BUILD_DIR = os.path.join(BASE_DIR, ".build")

# All lambda function folders
FUNCTIONS = [
    "send_otp",
    "verify_otp",
    "cast_vote",
    "get_results",
    "create_election",
    "add_candidates",
    "get_posts",
    "export_results",
    "bulk_upload_voters",
    "admin_login",
    "admin_stats",
    "get_elections",
    "get_candidates",
]

def zip_function(function_name):
    function_path = os.path.join(BASE_DIR, function_name)
    zip_path = os.path.join(BUILD_DIR, f"{function_name}.zip")

    if not os.path.exists(function_path):
        print(f"❌ Skipping {function_name} (folder not found)")
        return

    print(f"🔧 Building {function_name}.zip...")

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(function_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, function_path)
                z.write(file_path, arcname)

    print(f"✅ Created: {zip_path}")

def main():
    # Create .build folder if not exists
    if not os.path.exists(BUILD_DIR):
        os.makedirs(BUILD_DIR)

    for func in FUNCTIONS:
        zip_function(func)

    print("\n🎉 All Lambda functions packaged successfully!")

if __name__ == "__main__":
    main()
