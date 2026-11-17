import os
import shutil
import subprocess
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

def cleanup_backup(backup_dir):
    try:
        shutil.rmtree(backup_dir)
    except OSError as exc:
        print(f"Could not remove backup at {backup_dir}: {exc}", file=sys.stderr)

def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: update.py <release_dir>")

    source_file = Path(sys.argv[1]) / "health.py"

    if not source_file.is_file():
        sys.exit(f'File not found: {source_file}')

    target_file = Path('/opt/linux-health-checker/health.py')

    backup_dir = Path(tempfile.mkdtemp(prefix="health-checker-backup-"))
    backup_file = backup_dir / "health.py"
    try:
        shutil.copy2(target_file, backup_file)
        replace_file(source_file, target_file)
    except OSError:
        cleanup_backup(backup_dir)
        raise

    try:
        smoke_result = subprocess.run(
            ["bash", "deploy/smoke_check.sh"],
            cwd=source_file.parent,
            check=False,
            )
        smoke_passed = smoke_result.returncode == 0
    except OSError as exc:
        print(f"Could not start smoke check: {exc}", file=sys.stderr)
        smoke_passed = False
        

    if not smoke_passed:
        try:
            replace_file(backup_file, target_file)
        except OSError as exc:
            sys.exit(f"Rollback failed: {exc}. Backup kept at {backup_file}")

        try:
            rollback_result = subprocess.run(
                ["bash", "deploy/smoke_check.sh"],
                cwd=source_file.parent,
                check=False,
            )
        except OSError as exc:
            sys.exit(
                f"Deployment failed. Previous version restored, "
                f"but its smoke check could not start: {exc}. "
                f"Backup kept at {backup_file}"
            )

        if rollback_result.returncode == 0:
            cleanup_backup(backup_dir)
            sys.exit("Deployment failed. Previous version restored and verified.")
        else:
            sys.exit(f"Deployment failed. Previous version restored, but its smoke check failed. Backup: {backup_file}")

    cleanup_backup(backup_dir)

if __name__ == "__main__":
    main()