"""
Database Handler - Modul pengelolaan database SQLite
====================================================
Menangani semua operasi CRUD untuk data inspeksi perkebunan.
Tabel 'inspections' dibuat otomatis saat inisialisasi.
"""

import sqlite3
import os
from datetime import datetime


class DatabaseHandler:
    """
    Handler database SQLite untuk menyimpan dan mengelola data inspeksi perkebunan.
    
    Fitur:
    - Auto-create tabel saat pertama kali dijalankan
    - Insert, read, update, delete inspeksi
    - Tracking status upload (uploaded/pending)
    - Thread-safe dengan row_factory untuk output dictionary
    """

    # Definisi kolom tabel inspeksi beserta tipe datanya
    COLUMNS = [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("nama_perusahaan", "TEXT"),
        ("nama_kebun", "TEXT"),
        ("afdeling", "TEXT"),
        ("no_blok", "TEXT"),
        ("tahun_tanam", "TEXT"),
        ("luas", "REAL"),
        ("jumlah_terserang", "INTEGER"),
        ("tanggal_pengambilan", "TEXT"),
        ("latitude", "REAL"),
        ("longitude", "REAL"),
        ("nama_lokasi", "TEXT"),
        ("nitrogen", "REAL"),
        ("phosphor", "REAL"),
        ("kalium", "REAL"),
        ("ph", "REAL"),
        ("ec", "REAL"),
        ("moisture", "REAL"),
        ("temperature", "REAL"),
        ("mq3_raw", "REAL"),
        ("mq135_raw", "REAL"),
        ("mq138_raw", "REAL"),
        ("tgs2600_raw", "REAL"),
        ("tgs2602_raw", "REAL"),
        ("gas_data", "TEXT"),
        ("foto_path", "TEXT"),
        ("video_path", "TEXT"),
        ("tree_node_id", "TEXT"),
        ("tree_age", "TEXT"),
        ("tree_health_status", "TEXT"),
        ("spatial_compass_neighbors", "TEXT"),
        ("surveyor_name", "TEXT"),
        ("field_notes", "TEXT"),
        ("timestamp", "TEXT"),
        ("uploaded", "INTEGER DEFAULT 0"),
    ]

    def __init__(self, db_path: str = None):
        """
        Inisialisasi DatabaseHandler.

        Args:
            db_path: Path ke file database SQLite.
                     Jika None, default ke <project_root>/data.db
        """
        if db_path is None:
            # Tentukan project root (satu level di atas folder 'database/')
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(project_root, "data.db")

        self.db_path = db_path

        # Pastikan direktori untuk file database sudah ada
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        # Buat tabel otomatis saat inisialisasi
        self.create_table()

    def _get_connection(self) -> sqlite3.Connection:
        """
        Buat koneksi baru ke database.
        Menggunakan row_factory agar hasil query berupa dictionary.

        Returns:
            sqlite3.Connection dengan row_factory = sqlite3.Row
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_table(self):
        """
        Buat tabel 'inspections' jika belum ada.
        Definisi kolom diambil dari COLUMNS class attribute.
        """
        columns_sql = ",\n            ".join(
            f"{name} {dtype}" for name, dtype in self.COLUMNS
        )
        query = f"""
            CREATE TABLE IF NOT EXISTS inspections (
            {columns_sql}
            )
        """
        conn = self._get_connection()
        try:
            conn.execute(query)
            conn.commit()

            # Auto-migration: check if video_path & spatial tree columns exist
            cursor = conn.execute("PRAGMA table_info(inspections)")
            existing_cols = [row["name"] for row in cursor.fetchall()]
            
            for col_name, col_type in [
                ("video_path", "TEXT"),
                ("tree_node_id", "TEXT"),
                ("tree_age", "TEXT"),
                ("tree_health_status", "TEXT"),
                ("spatial_compass_neighbors", "TEXT"),
                ("surveyor_name", "TEXT"),
                ("field_notes", "TEXT"),
                ("mq3_raw", "REAL"),
                ("mq135_raw", "REAL"),
                ("mq138_raw", "REAL"),
                ("tgs2600_raw", "REAL"),
                ("tgs2602_raw", "REAL"),
                ("gas_data", "TEXT")
            ]:
                if col_name not in existing_cols:
                    conn.execute(f"ALTER TABLE inspections ADD COLUMN {col_name} {col_type}")
                    conn.commit()
                    print(f"[DB MIGRATE] Added {col_name} column to SQLite table 'inspections'.")
        except sqlite3.Error as e:
            print(f"[DB ERROR] Gagal membuat/mengubah tabel: {e}")
            raise
        finally:
            conn.close()

    def insert_inspection(self, data: dict) -> int:
        """
        Masukkan data inspeksi baru ke database.

        Args:
            data: Dictionary berisi nama kolom sebagai key dan nilainya.
                  Kolom 'timestamp' akan diisi otomatis jika tidak disediakan.
                  Kolom 'id' diabaikan (auto-increment).

        Returns:
            ID baris yang baru dimasukkan.

        Raises:
            sqlite3.Error: Jika terjadi kesalahan saat insert.
        """
        # Tambahkan timestamp otomatis jika belum ada
        if "timestamp" not in data or not data["timestamp"]:
            data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Filter hanya kolom yang valid (hindari kolom 'id')
        valid_columns = [name for name, _ in self.COLUMNS if name != "id"]
        filtered_data = {k: v for k, v in data.items() if k in valid_columns}

        if not filtered_data:
            raise ValueError("Data kosong atau tidak ada kolom yang valid.")

        columns = ", ".join(filtered_data.keys())
        placeholders = ", ".join(["?"] * len(filtered_data))
        values = list(filtered_data.values())

        query = f"INSERT INTO inspections ({columns}) VALUES ({placeholders})"

        conn = self._get_connection()
        try:
            cursor = conn.execute(query, values)
            conn.commit()
            inserted_id = cursor.lastrowid
            return inserted_id
        except sqlite3.Error as e:
            print(f"[DB ERROR] Gagal insert inspeksi: {e}")
            raise
        finally:
            conn.close()

    def get_all_inspections(self) -> list:
        """
        Ambil semua data inspeksi, diurutkan berdasarkan timestamp terbaru.

        Returns:
            List of dict, masing-masing merepresentasikan satu baris inspeksi.
        """
        query = "SELECT * FROM inspections ORDER BY timestamp DESC"
        conn = self._get_connection()
        try:
            cursor = conn.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"[DB ERROR] Gagal mengambil data inspeksi: {e}")
            return []
        finally:
            conn.close()

    def get_inspection_by_id(self, inspection_id: int) -> dict:
        """
        Ambil satu data inspeksi berdasarkan ID.

        Args:
            inspection_id: ID inspeksi yang dicari.

        Returns:
            Dictionary data inspeksi, atau None jika tidak ditemukan.
        """
        query = "SELECT * FROM inspections WHERE id = ?"
        conn = self._get_connection()
        try:
            cursor = conn.execute(query, (inspection_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"[DB ERROR] Gagal mengambil inspeksi ID {inspection_id}: {e}")
            return None
        finally:
            conn.close()

    def delete_inspection(self, inspection_id: int):
        """
        Hapus satu data inspeksi berdasarkan ID.

        Args:
            inspection_id: ID inspeksi yang akan dihapus.
        """
        query = "DELETE FROM inspections WHERE id = ?"
        conn = self._get_connection()
        try:
            conn.execute(query, (inspection_id,))
            conn.commit()
        except sqlite3.Error as e:
            print(f"[DB ERROR] Gagal menghapus inspeksi ID {inspection_id}: {e}")
            raise
        finally:
            conn.close()

    def delete_multiple(self, ids: list):
        """
        Hapus beberapa data inspeksi sekaligus berdasarkan list ID.

        Args:
            ids: List berisi ID-ID inspeksi yang akan dihapus.
        """
        if not ids:
            return

        placeholders = ", ".join(["?"] * len(ids))
        query = f"DELETE FROM inspections WHERE id IN ({placeholders})"

        conn = self._get_connection()
        try:
            conn.execute(query, ids)
            conn.commit()
        except sqlite3.Error as e:
            print(f"[DB ERROR] Gagal menghapus {len(ids)} inspeksi: {e}")
            raise
        finally:
            conn.close()

    def mark_uploaded(self, inspection_id: int):
        """
        Tandai inspeksi sebagai sudah diupload (uploaded = 1).

        Args:
            inspection_id: ID inspeksi yang sudah diupload.
        """
        query = "UPDATE inspections SET uploaded = 1 WHERE id = ?"
        conn = self._get_connection()
        try:
            conn.execute(query, (inspection_id,))
            conn.commit()
        except sqlite3.Error as e:
            print(f"[DB ERROR] Gagal menandai upload ID {inspection_id}: {e}")
            raise
        finally:
            conn.close()

    def get_record_count(self) -> int:
        """
        Hitung total jumlah record inspeksi di database.

        Returns:
            Jumlah total record.
        """
        query = "SELECT COUNT(*) as total FROM inspections"
        conn = self._get_connection()
        try:
            cursor = conn.execute(query)
            row = cursor.fetchone()
            return row["total"] if row else 0
        except sqlite3.Error as e:
            print(f"[DB ERROR] Gagal menghitung record: {e}")
            return 0
        finally:
            conn.close()

    def get_pending_count(self) -> int:
        """
        Hitung jumlah record yang belum diupload (uploaded = 0).

        Returns:
            Jumlah record yang menunggu upload.
        """
        query = "SELECT COUNT(*) as total FROM inspections WHERE uploaded = 0"
        conn = self._get_connection()
        try:
            cursor = conn.execute(query)
            row = cursor.fetchone()
            return row["total"] if row else 0
        except sqlite3.Error as e:
            print(f"[DB ERROR] Gagal menghitung pending: {e}")
            return 0
        finally:
            conn.close()

    def __repr__(self) -> str:
        return f"DatabaseHandler(db_path='{self.db_path}')"


def get_db_handler(db_type: str = "sqlite", **kwargs):
    """
    Factory function untuk mendapatkan handler database (MySQL atau SQLite).

    Args:
        db_type: Tipe database, 'mysql' atau 'sqlite' (default: 'sqlite')
        **kwargs: Parameter opsional untuk koneksi (host, port, user, password, database, dll)

    Returns:
        Instance dari MySQLDatabaseHandler atau DatabaseHandler (SQLite).
    """
    db_type = db_type.lower()
    if db_type == "mysql":
        try:
            from .mysql_db_handler import MySQLDatabaseHandler
            return MySQLDatabaseHandler(**kwargs)
        except Exception as e:
            print(f"[DB WARNING] Gagal menginisialisasi MySQL ({e}). Beralih ke SQLite fallback...")
            return DatabaseHandler()
    else:
        return DatabaseHandler(db_path=kwargs.get("db_path", None))

