# backup/compression.py
# Handles compressing and decompressing backup files.
# Kept separate from connectors so any DB type can reuse the same logic.

import gzip
import shutil
import os

def compress_file(source_path: str, remove_original: bool = True) -> str:
    """Compress a file using gzip. Returns path to the .gz file."""
    compressed_path = source_path + ".gz"

    with open(source_path, 'rb') as f_in:
        with gzip.open(compressed_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    if remove_original:
        os.remove(source_path)

    return compressed_path


def decompress_file(compressed_path: str, output_path: str | None = None) -> str:
    """Decompress a .gz file. Returns path to the decompressed file."""
    if output_path is None:
        output_path = compressed_path.replace(".gz", "")

    with gzip.open(compressed_path, 'rb') as f_in:
        with open(output_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    return output_path