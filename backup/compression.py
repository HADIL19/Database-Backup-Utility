# backup/compression.py
# Handles compressing and decompressing backup files.
# Supports both single files (gzip) and folders (zip) —
# needed because MongoDB backups are directories, unlike SQLite/MySQL.

import gzip
import shutil
import os

def compress_file(source_path: str, remove_original: bool = True) -> str:
    """Compress a file or folder. Files use gzip (.gz), folders use zip (.zip)."""
    if os.path.isdir(source_path):
        # shutil.make_archive adds the extension itself, so pass the base name without it
        archive_base = source_path.rstrip(os.sep)
        archive_path = shutil.make_archive(archive_base, 'zip', source_path)

        if remove_original:
            shutil.rmtree(source_path)

        return archive_path

    else:
        compressed_path = source_path + ".gz"
        with open(source_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        if remove_original:
            os.remove(source_path)

        return compressed_path


def decompress_file(compressed_path: str, output_path: str | None = None) -> str:
    """Decompress a .gz file or .zip folder archive. Returns the resulting path."""
    if compressed_path.endswith(".zip"):
        if output_path is None:
            output_path = compressed_path.replace(".zip", "")
        shutil.unpack_archive(compressed_path, output_path, 'zip')
        return output_path

    else:
        if output_path is None:
            output_path = compressed_path.replace(".gz", "")
        with gzip.open(compressed_path, 'rb') as f_in:
            with open(output_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        return output_path