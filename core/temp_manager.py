# core/temp_manager.py

import os
import shutil


class TempManager:

    PROJECT_ROOT = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )

    @staticmethod
    def create_temp_dir(subfolder=None):

        temp_dir = os.path.join(
            TempManager.PROJECT_ROOT,
            "temp"
        )

        if subfolder:
            temp_dir = os.path.join(
                temp_dir,
                subfolder
            )

        os.makedirs(temp_dir, exist_ok=True)

        return temp_dir

    @staticmethod
    def delete_temp_subfolder(subfolder):

        target_dir = os.path.join(
            TempManager.PROJECT_ROOT,
            "temp",
            subfolder
        )

        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
            return True

        return False
"""
# Verify that the temp/ directory exists and create the subfolder
temp_dir = get_temp_dir()
print(f"✅ Temp directory exists: {temp_dir}")
temp_dir = get_temp_dir(subfolder="debug")
print(f"✅ Subfolder created: {temp_dir}")

# Verify that the temp/debug/ directory exists and delete it
deleted = del_temp_subfolder("debug")
if deleted:
    print("✅ Subfolder deleted: debug")
"""