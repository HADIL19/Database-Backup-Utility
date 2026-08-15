# tests/test_compression.py
from backup.compression import compress_file, decompress_file


def test_compress_and_decompress_roundtrip(tmp_path):
    """Compressing then decompressing should return the exact original content."""

    original_file = tmp_path / "data.txt"
    original_content = b"Hello, this is test data for compression."
    original_file.write_bytes(original_content)

    compressed_path = compress_file(str(original_file), remove_original=False)
    assert compressed_path.endswith(".gz")

    decompressed_path = decompress_file(compressed_path, str(tmp_path / "restored.txt"))
    restored_content = open(decompressed_path, "rb").read()

    assert restored_content == original_content


def test_compress_removes_original_by_default(tmp_path):
    """By default, compress_file should delete the uncompressed source."""
    import os

    original_file = tmp_path / "data.txt"
    original_file.write_bytes(b"some data")

    compress_file(str(original_file))  # remove_original defaults to True

    assert not os.path.exists(original_file)