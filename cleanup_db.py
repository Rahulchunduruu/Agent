"""
cleanup_db.py — Maintenance script for chatbot.db (LangGraph SqliteSaver storage).

What it does:
  1. Keeps only the latest KEEP checkpoints per thread (deletes the rest)
  2. Deletes orphaned rows in the 'writes' table
  3. Runs PRAGMA wal_checkpoint(TRUNCATE) to fold the WAL file back in
  4. Runs VACUUM to reclaim disk space

Why: LangGraph saves a FULL snapshot of the conversation at every step,
so the DB grows O(n^2) with conversation length. Pruning old checkpoints
is safe — only the ability to rewind to old states is lost.

Usage:  python cleanup_db.py     (stop the Streamlit app first)
"""

import os
import sqlite3

DB_PATH = "chatbot.db"
KEEP = 10  # latest checkpoints to keep per thread


def main():
    if not os.path.exists(DB_PATH):
        print("No {} found. Nothing to do.".format(DB_PATH))
        return

    before_mb = os.path.getsize(DB_PATH) / (1024 * 1024)
    wal = DB_PATH + "-wal"
    wal_mb = os.path.getsize(wal) / (1024 * 1024) if os.path.exists(wal) else 0

    conn = sqlite3.connect(DB_PATH, timeout=15)
    cur = conn.cursor()

    total_ckpts = cur.execute("SELECT COUNT(*) FROM checkpoints").fetchone()[0]
    threads = cur.execute("SELECT COUNT(DISTINCT thread_id) FROM checkpoints").fetchone()[0]
    print("Before: {:.1f} MB (+{:.1f} MB WAL) | checkpoints: {} | threads: {}".format(
        before_mb, wal_mb, total_ckpts, threads))

    # 1. Keep only the latest KEEP checkpoints per thread
    #    (checkpoint_id is a time-sortable UUID, so DESC = newest first)
    cur.execute(
        "DELETE FROM checkpoints WHERE rowid NOT IN ("
        "  SELECT rowid FROM ("
        "    SELECT rowid, ROW_NUMBER() OVER ("
        "      PARTITION BY thread_id, checkpoint_ns ORDER BY checkpoint_id DESC"
        "    ) AS rn FROM checkpoints"
        "  ) WHERE rn <= ?"
        ")",
        (KEEP,),
    )
    pruned_ckpts = cur.rowcount

    # 2. Delete orphaned writes (writes whose checkpoint no longer exists)
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
    print("Pruned: {} old checkpoints, {} orphaned writes".format(pruned_ckpts, pruned_writes))

    # 3. Fold WAL back into the main DB
    cur.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    # 4. Reclaim disk space
    cur.execute("VACUUM")
    conn.close()

    after_mb = os.path.getsize(DB_PATH) / (1024 * 1024)
    print("After:  {:.1f} MB | reclaimed {:.1f} MB".format(after_mb, before_mb + wal_mb - after_mb))


if __name__ == "__main__":
    main()
