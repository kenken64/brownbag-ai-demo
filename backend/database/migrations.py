"""
Database Migration Scripts for AI Crypto Trading Bot
Handles database schema updates and data migrations
Version: 1.0
"""

import sqlite3
import logging
import os
from datetime import datetime
from typing import List, Callable

logger = logging.getLogger(__name__)


class Migration:
    """Base class for database migrations"""

    def __init__(self, version: str, description: str):
        self.version = version
        self.description = description

    def up(self, conn: sqlite3.Connection):
        """Apply migration"""
        raise NotImplementedError

    def down(self, conn: sqlite3.Connection):
        """Rollback migration"""
        raise NotImplementedError


class MigrationManager:
    """Manages database migrations"""

    def __init__(self, db_path: str = "trading_bot.db"):
        self.db_path = db_path
        self.migrations: List[Migration] = []
        self._initialize_migration_table()

    def _initialize_migration_table(self):
        """Create migration tracking table if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT UNIQUE NOT NULL,
                description TEXT,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def register_migration(self, migration: Migration):
        """Register a migration"""
        self.migrations.append(migration)

    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT version FROM schema_migrations ORDER BY applied_at")
        versions = [row[0] for row in cursor.fetchall()]

        conn.close()
        return versions

    def apply_migration(self, migration: Migration):
        """Apply a single migration"""
        conn = sqlite3.connect(self.db_path)

        try:
            logger.info(f"Applying migration {migration.version}: {migration.description}")

            # Apply migration
            migration.up(conn)

            # Record migration
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
                (migration.version, migration.description)
            )

            conn.commit()
            logger.info(f"Migration {migration.version} applied successfully")

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to apply migration {migration.version}: {e}")
            raise

        finally:
            conn.close()

    def rollback_migration(self, migration: Migration):
        """Rollback a single migration"""
        conn = sqlite3.connect(self.db_path)

        try:
            logger.info(f"Rolling back migration {migration.version}: {migration.description}")

            # Rollback migration
            migration.down(conn)

            # Remove migration record
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM schema_migrations WHERE version = ?",
                (migration.version,)
            )

            conn.commit()
            logger.info(f"Migration {migration.version} rolled back successfully")

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to rollback migration {migration.version}: {e}")
            raise

        finally:
            conn.close()

    def migrate_up(self):
        """Apply all pending migrations"""
        applied = self.get_applied_migrations()
        pending = [m for m in self.migrations if m.version not in applied]

        if not pending:
            logger.info("No pending migrations")
            return

        logger.info(f"Applying {len(pending)} pending migrations")

        for migration in pending:
            self.apply_migration(migration)

        logger.info("All migrations applied successfully")

    def migrate_down(self, steps: int = 1):
        """Rollback specified number of migrations"""
        applied = self.get_applied_migrations()

        if not applied:
            logger.info("No migrations to rollback")
            return

        # Get migrations to rollback
        to_rollback = applied[-steps:]

        for version in reversed(to_rollback):
            migration = next((m for m in self.migrations if m.version == version), None)
            if migration:
                self.rollback_migration(migration)

        logger.info(f"Rolled back {len(to_rollback)} migrations")


# ============================================================================
# MIGRATION DEFINITIONS
# ============================================================================

class AddIndexesMigration(Migration):
    """Add performance indexes to database tables"""

    def __init__(self):
        super().__init__("001_add_indexes", "Add performance indexes")

    def up(self, conn: sqlite3.Connection):
        cursor = conn.cursor()

        # Add indexes if they don't exist
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_signals_trading_pair ON signals(trading_pair)",
            "CREATE INDEX IF NOT EXISTS idx_signals_signal_type ON signals(signal_type)",
            "CREATE INDEX IF NOT EXISTS idx_trades_trading_pair ON trades(trading_pair)",
            "CREATE INDEX IF NOT EXISTS idx_trades_signal_id ON trades(signal_id)",
            "CREATE INDEX IF NOT EXISTS idx_bot_status_bot_name ON bot_status(bot_name)",
            "CREATE INDEX IF NOT EXISTS idx_model_checkpoints_version ON model_checkpoints(version)",
            "CREATE INDEX IF NOT EXISTS idx_chart_analyses_trading_pair ON chart_analyses(trading_pair)",
            "CREATE INDEX IF NOT EXISTS idx_performance_metrics_period ON performance_metrics(period)",
            "CREATE INDEX IF NOT EXISTS idx_correlation_data_assets ON correlation_data(asset1, asset2)",
            "CREATE INDEX IF NOT EXISTS idx_cost_analytics_api_name ON cost_analytics(api_name)",
            "CREATE INDEX IF NOT EXISTS idx_news_cache_article_url ON news_cache(article_url)"
        ]

        for index_sql in indexes:
            cursor.execute(index_sql)

        conn.commit()

    def down(self, conn: sqlite3.Connection):
        cursor = conn.cursor()

        # Drop indexes
        indexes = [
            "DROP INDEX IF EXISTS idx_signals_trading_pair",
            "DROP INDEX IF EXISTS idx_signals_signal_type",
            "DROP INDEX IF EXISTS idx_trades_trading_pair",
            "DROP INDEX IF EXISTS idx_trades_signal_id",
            "DROP INDEX IF EXISTS idx_bot_status_bot_name",
            "DROP INDEX IF EXISTS idx_model_checkpoints_version",
            "DROP INDEX IF EXISTS idx_chart_analyses_trading_pair",
            "DROP INDEX IF EXISTS idx_performance_metrics_period",
            "DROP INDEX IF EXISTS idx_correlation_data_assets",
            "DROP INDEX IF EXISTS idx_cost_analytics_api_name",
            "DROP INDEX IF EXISTS idx_news_cache_article_url"
        ]

        for index_sql in indexes:
            cursor.execute(index_sql)

        conn.commit()


class AddDataRetentionMigration(Migration):
    """Add data retention tracking columns"""

    def __init__(self):
        super().__init__("002_data_retention", "Add data retention tracking")

    def up(self, conn: sqlite3.Connection):
        cursor = conn.cursor()

        # Add retention columns to tables (if they don't exist)
        tables_to_update = [
            "ALTER TABLE signals ADD COLUMN retention_days INTEGER DEFAULT 30",
            "ALTER TABLE chart_analyses ADD COLUMN retention_days INTEGER DEFAULT 30",
            "ALTER TABLE cost_analytics ADD COLUMN retention_days INTEGER DEFAULT 90"
        ]

        for sql in tables_to_update:
            try:
                cursor.execute(sql)
            except sqlite3.OperationalError as e:
                # Column may already exist
                if "duplicate column" not in str(e).lower():
                    raise

        conn.commit()

    def down(self, conn: sqlite3.Connection):
        # SQLite doesn't support DROP COLUMN easily
        # Would require table recreation
        logger.warning("Rollback for data retention migration requires manual table recreation")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def cleanup_old_data(db_path: str = "trading_bot.db"):
    """
    Clean up old data based on retention policies

    Retention policies:
    - signals: 30 days
    - chart_analyses: 30 days
    - bot_status: 7 days
    - cost_analytics: 90 days
    - news_cache: 7 days
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Calculate retention dates
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    retention_periods = {
        'signals': now - timedelta(days=30),
        'chart_analyses': now - timedelta(days=30),
        'bot_status': now - timedelta(days=7),
        'cost_analytics': now - timedelta(days=90),
        'news_cache': now - timedelta(days=7)
    }

    deleted_counts = {}

    for table, cutoff_date in retention_periods.items():
        try:
            cursor.execute(
                f"DELETE FROM {table} WHERE timestamp < ?",
                (cutoff_date.isoformat(),)
            )
            deleted_counts[table] = cursor.rowcount
        except Exception as e:
            logger.error(f"Error cleaning up {table}: {e}")

    conn.commit()
    conn.close()

    logger.info(f"Cleanup complete: {deleted_counts}")
    return deleted_counts


def vacuum_database(db_path: str = "trading_bot.db"):
    """
    Optimize database by reclaiming unused space

    This operation can take a while for large databases
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    logger.info("Running VACUUM on database...")

    try:
        cursor.execute("VACUUM")
        logger.info("VACUUM completed successfully")
    except Exception as e:
        logger.error(f"Error running VACUUM: {e}")
        raise
    finally:
        conn.close()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize migration manager
    manager = MigrationManager()

    # Register migrations
    manager.register_migration(AddIndexesMigration())
    manager.register_migration(AddDataRetentionMigration())

    # Apply migrations
    manager.migrate_up()

    logger.info("Migration process completed")
