"""SQLite ALTER TABLE migration for Sprint 7 schema changes."""
import os
import sqlite3


def migrate():
    db_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "investment.db")
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}, skipping migration.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cols = [row[1] for row in cursor.execute("PRAGMA table_info(agent_tasks)").fetchall()]

    migrations = [
        ("progress_json", "ALTER TABLE agent_tasks ADD COLUMN progress_json TEXT DEFAULT '{}'"),
        ("workflow_state_json", "ALTER TABLE agent_tasks ADD COLUMN workflow_state_json TEXT DEFAULT '{}'"),
        ("error_message", "ALTER TABLE agent_tasks ADD COLUMN error_message TEXT"),
        ("workspace_id", "ALTER TABLE agent_tasks ADD COLUMN workspace_id INTEGER REFERENCES workspaces(id)"),
        ("user_id", "ALTER TABLE agent_tasks ADD COLUMN user_id INTEGER REFERENCES users(id)"),
    ]

    for col_name, sql in migrations:
        if col_name not in cols:
            cursor.execute(sql)
            print(f"Added column: {col_name}")
        else:
            print(f"Column {col_name} already exists, skipping.")

    conn.commit()
    conn.close()
    print("Migration complete.")


if __name__ == "__main__":
    migrate()
