import os
import shutil
import sys
import tempfile
from pathlib import Path


def replace_file(source_file, target_file):
    target_dir = target_file.parent

    fd, temp_path = tempfile.mkstemp(dir=target_dir, prefix=".health.py.")
    os.close(fd)

    try:
        shutil.copyfile(source_file, temp_path)
        Path(temp_path).chmod(0o644)
        Path(temp_path).replace(target_file)
    finally:
        Path(temp_path).unlink(missing_ok=True)

def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: update.py <release_dir>")

    source_file = Path(sys.argv[1]) / "health.py"

    if not source_file.is_file():
        sys.exit(f'File not found: {source_file}')

    target_file = Path('/opt/linux-health-checker/health.py')
    replace_file(source_file, target_file)

if __name__ == "__main__":
    main()