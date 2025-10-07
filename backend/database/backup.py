"""
Automated Database Backup System for AI Crypto Trading Bot
Handles scheduled backups, retention, and restoration
Version: 1.0
"""

import os
import shutil
import sqlite3
import logging
import gzip
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
import schedule
import time

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages database backups"""

    def __init__(
        self,
        db_path: str = "trading_bot.db",
        backup_dir: str = "backups",
        max_backups: int = 30,
        compress: bool = True
    ):
        """
        Initialize backup manager

        Args:
            db_path: Path to database file
            backup_dir: Directory to store backups
            max_backups: Maximum number of backups to retain
            compress: Whether to compress backups with gzip
        """
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.max_backups = max_backups
        self.compress = compress

        # Create backup directory if it doesn't exist
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)

    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """
        Create a database backup

        Args:
            backup_name: Optional custom backup name

        Returns:
            Path to backup file
        """
        try:
            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if backup_name:
                filename = f"{backup_name}_{timestamp}.db"
            else:
                filename = f"trading_bot_backup_{timestamp}.db"

            backup_path = os.path.join(self.backup_dir, filename)

            # Check if source database exists
            if not os.path.exists(self.db_path):
                raise FileNotFoundError(f"Database file not found: {self.db_path}")

            # Use SQLite backup API for safe copying
            logger.info(f"Creating backup: {backup_path}")

            source_conn = sqlite3.connect(self.db_path)
            backup_conn = sqlite3.connect(backup_path)

            with backup_conn:
                source_conn.backup(backup_conn)

            source_conn.close()
            backup_conn.close()

            # Compress if requested
            if self.compress:
                compressed_path = backup_path + ".gz"
                logger.info(f"Compressing backup to {compressed_path}")

                with open(backup_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

                # Remove uncompressed backup
                os.remove(backup_path)
                backup_path = compressed_path

            # Get file size
            size_mb = os.path.getsize(backup_path) / (1024 * 1024)
            logger.info(f"Backup created successfully: {backup_path} ({size_mb:.2f} MB)")

            # Cleanup old backups
            self.cleanup_old_backups()

            return backup_path

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise

    def restore_backup(self, backup_path: str, target_path: Optional[str] = None):
        """
        Restore database from backup

        Args:
            backup_path: Path to backup file
            target_path: Target database path (defaults to self.db_path)
        """
        try:
            if target_path is None:
                target_path = self.db_path

            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Backup file not found: {backup_path}")

            logger.info(f"Restoring backup from {backup_path} to {target_path}")

            # Create backup of current database before restoring
            if os.path.exists(target_path):
                pre_restore_backup = target_path + f".pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy2(target_path, pre_restore_backup)
                logger.info(f"Created pre-restore backup: {pre_restore_backup}")

            # Decompress if needed
            temp_path = backup_path
            if backup_path.endswith('.gz'):
                temp_path = backup_path[:-3]  # Remove .gz extension
                logger.info(f"Decompressing backup...")

                with gzip.open(backup_path, 'rb') as f_in:
                    with open(temp_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

            # Copy backup to target
            shutil.copy2(temp_path, target_path)

            # Remove temporary decompressed file if created
            if temp_path != backup_path and os.path.exists(temp_path):
                os.remove(temp_path)

            logger.info("Backup restored successfully")

        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            raise

    def list_backups(self) -> List[dict]:
        """
        List all available backups

        Returns:
            List of backup information dictionaries
        """
        backups = []

        for filename in os.listdir(self.backup_dir):
            if filename.startswith('trading_bot_backup_'):
                filepath = os.path.join(self.backup_dir, filename)
                stat = os.stat(filepath)

                backups.append({
                    'filename': filename,
                    'path': filepath,
                    'size_mb': stat.st_size / (1024 * 1024),
                    'created_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'compressed': filename.endswith('.gz')
                })

        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x['created_at'], reverse=True)

        return backups

    def cleanup_old_backups(self):
        """Remove old backups beyond retention limit"""
        try:
            backups = self.list_backups()

            if len(backups) <= self.max_backups:
                return

            # Delete oldest backups
            to_delete = backups[self.max_backups:]

            logger.info(f"Cleaning up {len(to_delete)} old backups")

            for backup in to_delete:
                try:
                    os.remove(backup['path'])
                    logger.info(f"Deleted old backup: {backup['filename']}")
                except Exception as e:
                    logger.error(f"Failed to delete backup {backup['filename']}: {e}")

        except Exception as e:
            logger.error(f"Error during backup cleanup: {e}")

    def verify_backup(self, backup_path: str) -> bool:
        """
        Verify backup integrity

        Args:
            backup_path: Path to backup file

        Returns:
            True if backup is valid, False otherwise
        """
        try:
            # Decompress if needed
            temp_path = backup_path
            if backup_path.endswith('.gz'):
                temp_path = backup_path + '.tmp'
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(temp_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

            # Try to open database
            conn = sqlite3.connect(temp_path)
            cursor = conn.cursor()

            # Run integrity check
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()

            conn.close()

            # Remove temp file if created
            if temp_path != backup_path and os.path.exists(temp_path):
                os.remove(temp_path)

            is_valid = result[0] == 'ok'

            if is_valid:
                logger.info(f"Backup verified successfully: {backup_path}")
            else:
                logger.error(f"Backup integrity check failed: {backup_path}")

            return is_valid

        except Exception as e:
            logger.error(f"Error verifying backup {backup_path}: {e}")
            return False

    def schedule_daily_backup(self, hour: int = 2, minute: int = 0):
        """
        Schedule daily automated backups

        Args:
            hour: Hour of day (0-23)
            minute: Minute of hour (0-59)
        """
        schedule_time = f"{hour:02d}:{minute:02d}"

        schedule.every().day.at(schedule_time).do(self.create_backup)

        logger.info(f"Scheduled daily backup at {schedule_time}")

    def run_scheduler(self):
        """Run the backup scheduler (blocking)"""
        logger.info("Starting backup scheduler")

        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


class BackupService:
    """Background service for automated backups"""

    def __init__(self, backup_manager: BackupManager):
        self.backup_manager = backup_manager
        self.running = False

    def start(self):
        """Start the backup service"""
        self.running = True
        logger.info("Backup service started")

        # Schedule daily backups at 2 AM
        self.backup_manager.schedule_daily_backup(hour=2, minute=0)

        # Run scheduler
        try:
            self.backup_manager.run_scheduler()
        except KeyboardInterrupt:
            logger.info("Backup service stopped by user")
            self.stop()

    def stop(self):
        """Stop the backup service"""
        self.running = False
        schedule.clear()
        logger.info("Backup service stopped")


# ============================================================================
# CLI FUNCTIONS
# ============================================================================

def backup_now():
    """Create a backup immediately"""
    manager = BackupManager()
    backup_path = manager.create_backup()
    print(f"Backup created: {backup_path}")


def list_backups():
    """List all available backups"""
    manager = BackupManager()
    backups = manager.list_backups()

    if not backups:
        print("No backups found")
        return

    print(f"\nFound {len(backups)} backups:\n")
    for i, backup in enumerate(backups, 1):
        print(f"{i}. {backup['filename']}")
        print(f"   Size: {backup['size_mb']:.2f} MB")
        print(f"   Created: {backup['created_at']}")
        print(f"   Compressed: {backup['compressed']}")
        print()


def restore_latest():
    """Restore from the latest backup"""
    manager = BackupManager()
    backups = manager.list_backups()

    if not backups:
        print("No backups found")
        return

    latest = backups[0]
    print(f"Restoring from latest backup: {latest['filename']}")

    response = input("Are you sure? This will overwrite the current database (y/N): ")
    if response.lower() == 'y':
        manager.restore_backup(latest['path'])
        print("Backup restored successfully")
    else:
        print("Restore cancelled")


def verify_backups():
    """Verify all backups"""
    manager = BackupManager()
    backups = manager.list_backups()

    if not backups:
        print("No backups found")
        return

    print(f"Verifying {len(backups)} backups...\n")

    valid_count = 0
    for backup in backups:
        is_valid = manager.verify_backup(backup['path'])
        status = "OK" if is_valid else "FAILED"
        print(f"{backup['filename']}: {status}")

        if is_valid:
            valid_count += 1

    print(f"\n{valid_count}/{len(backups)} backups are valid")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    import sys

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    if len(sys.argv) < 2:
        print("Usage: python backup.py [backup|list|restore|verify|service]")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'backup':
        backup_now()
    elif command == 'list':
        list_backups()
    elif command == 'restore':
        restore_latest()
    elif command == 'verify':
        verify_backups()
    elif command == 'service':
        manager = BackupManager()
        service = BackupService(manager)
        service.start()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
