import sqlite3
import os
from datetime import datetime
from flet import StoragePaths, FletUnsupportedPlatformException


class Database:
    def __init__(self):
        self.db_path = None
        self.conn = None
    
    async def initialize(self):
        """Initialize database with cross-platform path."""
        storage_paths = StoragePaths()
        try:
            documents_dir = await storage_paths.get_application_documents_directory()
            self.db_path = os.path.join(documents_dir, "time_tracker.db")
        except FletUnsupportedPlatformException:
            # Fallback for web mode or unsupported platforms
            self.db_path = ":memory:"
        
        # Connect and create tables
        self.conn = sqlite3.connect(self.db_path)
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Entries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                date DATE NOT NULL,
                hours REAL NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)
        
        self.conn.commit()
    
    # Project operations
    def create_project(self, name: str) -> int:
        """Create a new project and return its ID."""
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO projects (name) VALUES (?)", (name,))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_all_projects(self):
        """Get all projects."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, created_at FROM projects ORDER BY name")
        return cursor.fetchall()
    
    def get_project(self, project_id: int):
        """Get a specific project by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, created_at FROM projects WHERE id = ?", (project_id,))
        return cursor.fetchone()
    
    def update_project(self, project_id: int, name: str):
        """Update a project name."""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE projects SET name = ? WHERE id = ?", (name, project_id))
        self.conn.commit()
    
    def delete_project(self, project_id: int):
        """Delete a project and all its entries."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM entries WHERE project_id = ?", (project_id,))
        cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        self.conn.commit()
    
    # Entry operations
    def create_entry(self, project_id: int, date: str, hours: float, description: str) -> int:
        """Create a new entry and return its ID."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO entries (project_id, date, hours, description) VALUES (?, ?, ?, ?)",
            (project_id, date, hours, description)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def get_entries_for_project(self, project_id: int, from_date: str = None, to_date: str = None):
        """Get entries for a project, optionally filtered by date range."""
        cursor = self.conn.cursor()
        
        if from_date and to_date:
            cursor.execute(
                """SELECT id, date, hours, description, created_at 
                   FROM entries 
                   WHERE project_id = ? AND date BETWEEN ? AND ?
                   ORDER BY date DESC""",
                (project_id, from_date, to_date)
            )
        elif from_date:
            cursor.execute(
                """SELECT id, date, hours, description, created_at 
                   FROM entries 
                   WHERE project_id = ? AND date >= ?
                   ORDER BY date DESC""",
                (project_id, from_date)
            )
        elif to_date:
            cursor.execute(
                """SELECT id, date, hours, description, created_at 
                   FROM entries 
                   WHERE project_id = ? AND date <= ?
                   ORDER BY date DESC""",
                (project_id, to_date)
            )
        else:
            cursor.execute(
                """SELECT id, date, hours, description, created_at 
                   FROM entries 
                   WHERE project_id = ?
                   ORDER BY date DESC""",
                (project_id,)
            )
        
        return cursor.fetchall()
    
    def get_entry(self, entry_id: int):
        """Get a specific entry by ID."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, project_id, date, hours, description, created_at FROM entries WHERE id = ?",
            (entry_id,)
        )
        return cursor.fetchone()
    
    def update_entry(self, entry_id: int, date: str, hours: float, description: str):
        """Update an entry."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE entries SET date = ?, hours = ?, description = ? WHERE id = ?",
            (date, hours, description, entry_id)
        )
        self.conn.commit()
    
    def delete_entry(self, entry_id: int):
        """Delete an entry."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        self.conn.commit()
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()