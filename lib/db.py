"""SQLite database helpers for account state tracking"""

import sqlite3
import csv
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "accounts.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS accounts (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            region TEXT NOT NULL,
            proxy TEXT,
            
            status TEXT DEFAULT queued,
            current_step TEXT,
            
            bc_id TEXT,
            bc_type TEXT DEFAULT whitehat,
            campaign_id TEXT,
            campaign_status TEXT,
            
            -- Batch settings
            batch_id TEXT,
            destination_url TEXT,
            budget REAL,
            currency TEXT,
            timezone TEXT,
            schedule_start TEXT,
            auto_pause INTEGER DEFAULT 1,
            
            error_log TEXT,
            attempts INTEGER DEFAULT 0,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS sessions (
            account_id TEXT PRIMARY KEY,
            cookies TEXT,
            browser_state TEXT,
            last_screenshot TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_status ON accounts(status);
        CREATE INDEX IF NOT EXISTS idx_campaign_status ON accounts(campaign_status);
        CREATE INDEX IF NOT EXISTS idx_batch_id ON accounts(batch_id);
    """)
    
    conn.commit()
    conn.close()


def get_next_queued_account() -> Optional[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM accounts 
        WHERE status = queued 
        ORDER BY created_at ASC 
        LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_account(account_id: str) -> Optional[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def add_account(account_id: str, email: str, password: str, region: str, 
                proxy: str = None, batch_id: str = None, bc_type: str = "whitehat",
                destination_url: str = None, budget: float = None, 
                currency: str = None, timezone: str = None,
                schedule_start: str = None, auto_pause: bool = True) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO accounts (id, email, password, region, proxy, batch_id, 
                bc_type, destination_url, budget, currency, timezone, 
                schedule_start, auto_pause)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (account_id, email, password, region, proxy, batch_id,
              bc_type, destination_url, budget, currency, timezone,
              schedule_start, 1 if auto_pause else 0))
        conn.commit()
        print(f"[DB] Added account {account_id}")
        return True
    except sqlite3.IntegrityError:
        print(f"[DB] Account {account_id} already exists")
        return False
    finally:
        conn.close()


def update_account(account_id: str, **kwargs) -> bool:
    if not kwargs:
        return False
    
    conn = get_connection()
    cursor = conn.cursor()
    
    fields = list(kwargs.keys()) + ["updated_at"]
    values = list(kwargs.values()) + [datetime.now().isoformat()]
    set_clause = ", ".join([f"{f} = ?" for f in fields])
    
    cursor.execute(f"UPDATE accounts SET {set_clause} WHERE id = ?", values + [account_id])
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


def get_pending_campaigns() -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM accounts 
        WHERE campaign_id IS NOT NULL 
        AND campaign_status = pending
        AND auto_pause = 1
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_accounts_by_status(status: str) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts WHERE status = ?", (status,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_accounts_by_batch(batch_id: str) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts WHERE batch_id = ?", (batch_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def export_to_csv(filepath: str = None) -> str:
    if not filepath:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = Path(__file__).parent.parent / f"exports/accounts_{ts}.csv"
    
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print("[DB] No accounts to export")
        return ""
    
    headers = rows[0].keys()
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))
    
    print(f"[DB] Exported {len(rows)} accounts to {filepath}")
    return str(filepath)


# Initialize on import
init_db()
