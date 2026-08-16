"""Database maintenance helpers for LangGraph SqliteSaver storage (chatbot.db).

LangGraph saves a FULL snapshot of the conversation at every step, so the DB
grows O(n^2) with conversation length. prune_checkpoints() keeps only the
latest N checkpoints per thread and reclaims space via WAL checkpoint + VACUUM.
"""

import os
import sqlite3

DB_PATH = "chatbot.db"
KEEP_CHECKPOINTS = 10          # latest checkpoints to keep per thread
AUTO_CLEANUP_THRESHOLD_MB = 50  # run cleanup on startup if DB exceeds this


def prune_checkpoints(db_path=DB_PATH, keep=KEEP_CHECKPOINTS):
    """Keep only the latest `keep` checkpoints per thread; delete the rest,
    remove orphaned writes, fold the WAL file back in, and VACUUM.
    Returns (pruned_checkpoints, pruned_writes, size_before_mb, size_after_mb)."""
    if not os.path.exists(db_path):
        return 0, 0, 0.0, 0.0

    size_before = os.path.getsize(db_path) / (1024 * 1024)

    conn = sqlite3.connect(db_path, timeout=15)
    cur = conn.cursor()

    # checkpoint_id is a time-sortable UUID -> DESC = newest first
    cur.execute(
        "DELETE FROM checkpoints WHERE rowid NOT IN ("
        "  SELECT rowid FROM ("
        "    SELECT rowid, ROW_NUMBER() OVER ("
        "      PARTITION BY thread_id, checkpoint_ns ORDER BY checkpoint_id DESC"
        "    ) AS rn FROM checkpoints"
        "  ) WHERE rn <= ?"
        ")",
        (keep,),
    )
    pruned_ckpts = cur.rowcount

    cur.execute(
        "DELETE FROM writes WHERE NOT EXISTS ("
        "  SELECT 1 FROM checkpoints c"
        "  WHERE c.thread_id = writes.thread_id"
        "    AND c.checkpoint_ns = writes.checkpoint_ns"
        "    AND c.checkpoint_id = writes.checkpoint_id"
        ")"
    )
    pruned_writes = cur.rowcount
    conn.commit()

    cur.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    cur.execute("VACUUM")
    conn.close()

    size_after = os.path.getsize(db_path) / (1024 * 1024)
    return pruned_ckpts, pruned_writes, size_before, size_after


def cleanup_if_needed(db_path=DB_PATH, threshold_mb=AUTO_CLEANUP_THRESHOLD_MB):
    """Run prune_checkpoints() only if the DB file exceeds threshold_mb.
    Safe to call on every app startup."""
    if not os.path.exists(db_path):
        return None
    size_mb = os.path.getsize(db_path) / (1024 * 1024)
    if size_mb > threshold_mb:
        return prune_checkpoints(db_path)
    return None
