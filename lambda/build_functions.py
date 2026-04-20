#!/usr/bin/env python3
"""
Build script to package Lambda functions with shared lib dependencies.
Creates zip files with proper directory structure including lib/ files.
"""

import os
import shutil
import zipfile
from pathlib import Path


def create_lambda_package(function_name, source_dir, output_zip):
    """
    Create a zip package for a Lambda function including shared lib files.

    Args:
        function_name: Name of the function (e.g., 'send_otp')
        source_dir: Source directory containing index.py
        output_zip: Output path for the zip file
    """
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_zip), exist_ok=True)

    # Create a temporary staging directory
    staging_dir = f".staging_{function_name}"
    if os.path.exists(staging_dir):
        shutil.rmtree(staging_dir)
    os.makedirs(staging_dir)

    try:
        # Copy function's index.py
        src_index = os.path.join(source_dir, "index.py")
        if os.path.exists(src_index):
            shutil.copy2(src_index, os.path.join(staging_dir, "index.py"))

        # Copy lib directory
        lib_dir = os.path.join(os.path.dirname(source_dir), "..", "lib")
        dest_lib = os.path.join(staging_dir, "lib")
        if os.path.exists(lib_dir):
            shutil.copytree(lib_dir, dest_lib, dirs_exist_ok=True)

        # Create zip file
        with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(staging_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, staging_dir)
                    zipf.write(file_path, arcname)

        print(f"[OK] Created {output_zip}")

    finally:
        # Clean up staging directory
        if os.path.exists(staging_dir):
            shutil.rmtree(staging_dir)


def main():
    """Build all Lambda function packages."""
    lambda_dir = os.path.dirname(os.path.abspath(__file__))
    functions_dir = os.path.join(lambda_dir, "functions")
    build_dir = os.path.join(lambda_dir, ".build")

    # Create build directory
    os.makedirs(build_dir, exist_ok=True)

    # List of Lambda functions to package
    functions = [
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

    print("Building Lambda function packages...")
    for func_name in functions:
        source_dir = os.path.join(functions_dir, func_name)
        if os.path.exists(source_dir):
            output_zip = os.path.join(build_dir, f"{func_name}.zip")
            create_lambda_package(func_name, source_dir, output_zip)
        else:
            print(f"⚠ Function directory not found: {source_dir}")

    print("\nAll Lambda packages built successfully!")


if __name__ == "__main__":
    main()
