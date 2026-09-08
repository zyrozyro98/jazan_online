from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "jazan.db"


class Database:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.init_db()

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.connect()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS programs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                );

                CREATE TABLE IF NOT EXISTS sections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    program_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    UNIQUE(program_id, name),
                    FOREIGN KEY(program_id) REFERENCES programs(id)
                );

                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    university_id TEXT,
                    national_id TEXT,
                    program_id INTEGER NOT NULL,
                    section_id INTEGER NOT NULL,
                    FOREIGN KEY(program_id) REFERENCES programs(id),
                    FOREIGN KEY(section_id) REFERENCES sections(id)
                );

                CREATE TABLE IF NOT EXISTS automation_commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    command_type TEXT NOT NULL,
                    selector_type TEXT NOT NULL,
                    selector_value TEXT NOT NULL,
                    value_template TEXT,
                    wait_seconds REAL DEFAULT 0,
                    order_index INTEGER NOT NULL DEFAULT 0
                );
                """
            )
            conn.commit()
        finally:
            conn.close()

    def list_programs(self):
        conn = self.connect()
        try:
            return conn.execute("SELECT * FROM programs ORDER BY id").fetchall()
        finally:
            conn.close()

    def list_sections(self, program_id: int | None = None):
        conn = self.connect()
        try:
            if program_id is None:
                return conn.execute("SELECT * FROM sections ORDER BY id").fetchall()
            return conn.execute(
                "SELECT * FROM sections WHERE program_id = ? ORDER BY id",
                (program_id,),
            ).fetchall()
        finally:
            conn.close()

    def list_students(self, program_id: int | None = None, section_id: int | None = None):
        conn = self.connect()
        try:
            query = "SELECT s.*, p.name AS program_name, sec.name AS section_name FROM students s JOIN programs p ON p.id = s.program_id JOIN sections sec ON sec.id = s.section_id"
            params = []
            if program_id is not None:
                query += " WHERE s.program_id = ?"
                params.append(program_id)
            if section_id is not None:
                if params:
                    query += " AND s.section_id = ?"
                else:
                    query += " WHERE s.section_id = ?"
                params.append(section_id)
            query += " ORDER BY s.id"
            return conn.execute(query, tuple(params)).fetchall()
        finally:
            conn.close()

    def add_program(self, name: str):
        conn = self.connect()
        try:
            cur = conn.execute("INSERT INTO programs(name) VALUES (?)", (name,))
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def add_section(self, program_id: int, name: str):
        conn = self.connect()
        try:
            cur = conn.execute(
                "INSERT INTO sections(program_id, name) VALUES (?, ?)",
                (program_id, name),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def add_student(self, full_name: str, university_id: str, national_id: str, program_id: int, section_id: int):
        conn = self.connect()
        try:
            cur = conn.execute(
                "INSERT INTO students(full_name, university_id, national_id, program_id, section_id) VALUES (?, ?, ?, ?, ?)",
                (full_name, university_id, national_id, program_id, section_id),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def add_command(self, name: str, command_type: str, selector_type: str, selector_value: str, value_template: str | None, wait_seconds: float, order_index: int):
        conn = self.connect()
        try:
            cur = conn.execute(
                "INSERT INTO automation_commands(name, command_type, selector_type, selector_value, value_template, wait_seconds, order_index) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (name, command_type, selector_type, selector_value, value_template, wait_seconds, order_index),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def update_command(self, command_id: int, name: str, command_type: str, selector_type: str, selector_value: str, value_template: str | None, wait_seconds: float, order_index: int):
        conn = self.connect()
        try:
            conn.execute(
                "UPDATE automation_commands SET name = ?, command_type = ?, selector_type = ?, selector_value = ?, value_template = ?, wait_seconds = ?, order_index = ? WHERE id = ?",
                (name, command_type, selector_type, selector_value, value_template, wait_seconds, order_index, command_id),
            )
            conn.commit()
        finally:
            conn.close()

    def delete_command(self, command_id: int):
        conn = self.connect()
        try:
            conn.execute("DELETE FROM automation_commands WHERE id = ?", (command_id,))
            conn.commit()
        finally:
            conn.close()

    def list_commands(self):
        conn = self.connect()
        try:
            return conn.execute(
                "SELECT * FROM automation_commands ORDER BY order_index, id"
            ).fetchall()
        finally:
            conn.close()
