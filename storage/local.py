# storage/local.py
# Handles saving backup files to local disk.
# Kept separate so cloud storage backends (S3, GCS) can implement
# the same interface later without touching backup/connector logic.

import os
import shutil

class LocalStorage:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def save(self, source_path: str) -> str:
        """Move a backup file into the storage location. Returns final path."""
        filename = os.path.basename(source_path)
        dest_path = os.path.join(self.base_dir, filename)

        if os.path.abspath(source_path) != os.path.abspath(dest_path):
            shutil.move(source_path, dest_path)

        return dest_path