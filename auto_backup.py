import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

BACKUP_FOLDER = "auto_backups"
LAST_BACKUP_FILE = "last_backup.txt"

def should_backup(days=1):
    """Checks if a backup should run (once per X days)."""
    if not os.path.exists(LAST_BACKUP_FILE):
        return True

    with open(LAST_BACKUP_FILE, "r") as f:
        last = f.read().strip()
    if not last:
        return True

    last_date = datetime.strptime(last, "%Y-%m-%d")
    delta = (datetime.now() - last_date).days
    return delta >= days

def create_auto_backup():
    username = load_or_create_username()
    os.makedirs(BACKUP_FOLDER, exist_ok=True)

    backup_dir = f"auto_temp_{username}"
    zip_path = os.path.join(BACKUP_FOLDER, f"auto_backup_{username}.zip")
    os.makedirs(backup_dir, exist_ok=True)

    files = [
        f"{username}_keys.json",
        "inbox_history.txt",
        "usage_stats.json",
        "offline_queue.json",
        "groups.json"
    ]

    for file in files:
        if os.path.exists(file):
            shutil.copy(file, os.path.join(backup_dir, file))

    if os.path.exists("vault"):
        shutil.copytree("vault", os.path.join(backup_dir, "vault"), dirs_exist_ok=True)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in Path(backup_dir).rglob("*"):
            zipf.write(file, file.relative_to(backup_dir))

    shutil.rmtree(backup_dir)
    with open(LAST_BACKUP_FILE, "w") as f:
        f.write(datetime.now().strftime("%Y-%m-%d"))

    print(f"🛡️  Auto-backup created: {zip_path}")
