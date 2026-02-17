"""SQLite database helpers for account state tracking"""

import sqlite3
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "accounts.db"


def get_connection() -> sqlite3.Connection:
    """Get database connection with row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database with schema"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS accounts (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            region TEXT NOT NULL,
            proxy TEXT,
            
            status TEXT DEFAULT "queued",
            current_step TEXT,
            
            bc_id TEXT,
            campaign_id TEXT,
            campaign_status TEXT,
            
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
    """)
    
    conn.commit()
    conn.close()
    print(f"[DB] Initialized at {DB_PATH}")


def get_next_queued_account() -> Optional[Dict]:
    """Get next account with status=queued"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM accounts 
        WHERE status = "queued" 
        ORDER BY created_at ASC 
        LIMIT 1
    """)
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def get_account(account_id: str) -> Optional[Dict]:
    """Get account by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def add_account(account_id: str, email: str, password: str, region: str, proxy: str = None) -> bool:
    """Add new account to queue"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO accounts (id, email, password, region, proxy)
            VALUES (?, ?, ?, ?, ?)
        """, (account_id, email, password, region, proxy))
        conn.commit()
        print(f"[DB] Added account {account_id}")
        return True
    except sqlite3.IntegrityError:
        print(f"[DB] Account {account_id} already exists")
        return False
    finally:
        conn.close()


def update_account(account_id: str, **kwargs) -> bool:
    """Update account fields"""
    if not kwargs:
        return False
    
    conn = get_connection()
    cursor = conn.cursor()
    
    fields = list(kwargs.keys()) + ["updated_at"]
    values = list(kwargs.values()) + [datetime.now().isoformat()]
    
    set_clause = ", ".join([f"{f} = ?" for f in fields])
    
    cursor.execute(f"""
        UPDATE accounts SET {set_clause} WHERE id = ?
    """, values + [account_id])
    
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    
    return affected > 0


def get_pending_campaigns() -> List[Dict]:
    """Get accounts with pending campaigns to monitor"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM accounts 
        WHERE campaign_id IS NOT NULL 
        AND campaign_status = "pending"
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_accounts_by_status(status: str) -> List[Dict]:
    """Get all accounts with given status"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM accounts WHERE status = ?", (status,))
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


# Initialize database on import
init_db()
