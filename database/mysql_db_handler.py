"""
MySQL Database Handler - Modul pengelolaan database MySQL
=========================================================
Menangani semua operasi CRUD untuk data inspeksi perkebunan menggunakan MySQL.
Kompatibel secara interface dengan DatabaseHandler (SQLite).
"""

from datetime import datetime
import json
import os

try:
    import pymysql
    from pymysql.cursors import DictCursor
    HAS_PYMYSQL = True
except ImportError:
    HAS_PYMYSQL = False


class MySQLDatabaseHandler:
    """
    Handler database MySQL untuk menyimpan dan mengelola data inspeksi perkebunan.
    
    Fitur:
    - Auto-create database & tabel saat pertama kali dijalankan
    - Operasi CRUD (Insert, Read, Delete, Mark Uploaded)
    - Output dictionary row
    """

    COLUMNS = [
        ("id", "INT AUTO_INCREMENT PRIMARY KEY"),
        ("nama_perusahaan", "VARCHAR(255)"),
        ("nama_kebun", "VARCHAR(255)"),
        ("afdeling", "VARCHAR(100)"),
        ("no_blok", "VARCHAR(100)"),
        ("tahun_tanam", "VARCHAR(50)"),
        ("luas", "DOUBLE"),
        ("jumlah_terserang", "INT"),
        ("tanggal_pengambilan", "VARCHAR(100)"),
        ("latitude", "DOUBLE"),
        ("longitude", "DOUBLE"),
        ("nama_lokasi", "VARCHAR(255)"),
        ("nitrogen", "DOUBLE"),
        ("phosphor", "DOUBLE"),
        ("kalium", "DOUBLE"),
        ("ph", "DOUBLE"),
        ("ec", "DOUBLE"),
        ("moisture", "DOUBLE"),
        ("temperature", "DOUBLE"),
        ("foto_path", "TEXT"),
        ("video_path", "TEXT"),
        ("timestamp", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
        ("uploaded", "TINYINT DEFAULT 0"),
    ]

    def __init__(
        self,
        host: str = "localhost",
        port: int = 3306,
        user: str = "root",
        password: str = "",
        database: str = "sig_monitoring",
        auto_create_db: bool = True,
    ):
        """
        Inisialisasi MySQLDatabaseHandler.

        Args:
            host: Hostname server MySQL (default: 'localhost')
            port: Port MySQL (default: 3306)
            user: Username MySQL (default: 'root')
            password: Password MySQL (default: '')
            database: Nama database MySQL (default: 'sig_monitoring')
            auto_create_db: Apakah otomatis buat database & tabel jika belum ada (default: True)
        """
        if not HAS_PYMYSQL:
            raise ImportError(
                "Modul 'pymysql' belum terinstall. "
                "Silakan install dengan perintah: pip install pymysql"
            )

        self.config = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": database,
            "charset": "utf8mb4",
        }

        if auto_create_db:
            self._ensure_database_exists()
            self.create_table()

    def _get_connection(self, include_db: bool = True):
        """Buat koneksi ke server MySQL."""
        conn_config = self.config.copy()
        if not include_db:
            conn_config.pop("database", None)

        return pymysql.connect(
            host=conn_config["host"],
            port=conn_config["port"],
            user=conn_config["user"],
            password=conn_config["password"],
            database=conn_config.get("database"),
            charset=conn_config["charset"],
            cursorclass=DictCursor,
            autocommit=True,
        )

    def _ensure_database_exists(self):
        """Buat database jika belum ada."""
        try:
            conn = self._get_connection(include_db=False)
            db_name = self.config["database"]
            with conn.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{db_name}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
                )
            conn.close()
        except Exception as e:
            print(f"[MYSQL DB ERROR] Gagal membuat database '{self.config['database']}': {e}")
            raise

    def create_table(self):
        """Buat tabel 'inspections' jika belum ada di database MySQL."""
        columns_sql = ",\n            ".join(
            f"`{name}` {dtype}" for name, dtype in self.COLUMNS
        )
        query = f"""
            CREATE TABLE IF NOT EXISTS inspections (
            {columns_sql}
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query)
        except Exception as e:
            print(f"[MYSQL DB ERROR] Gagal membuat tabel inspections: {e}")
            raise
        finally:
            conn.close()

    def insert_inspection(self, data: dict) -> int:
        """
        Masukkan data inspeksi baru ke database MySQL.

        Args:
            data: Dictionary data inspeksi.

        Returns:
            ID baris yang baru dimasukkan.
        """
        if "timestamp" not in data or not data["timestamp"]:
            data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        valid_columns = [name for name, _ in self.COLUMNS if name != "id"]
        filtered_data = {k: v for k, v in data.items() if k in valid_columns}

        if not filtered_data:
            raise ValueError("Data kosong atau tidak ada kolom yang valid.")

        cols_str = ", ".join(f"`{k}`" for k in filtered_data.keys())
        placeholders = ", ".join(["%s"] * len(filtered_data))
        values = list(filtered_data.values())

        query = f"INSERT INTO inspections ({cols_str}) VALUES ({placeholders})"

        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, values)
                inserted_id = cursor.lastrowid
                return inserted_id
        except Exception as e:
            print(f"[MYSQL DB ERROR] Gagal insert inspeksi: {e}")
            raise
        finally:
            conn.close()

    def get_all_inspections(self) -> list:
        """Ambil semua data inspeksi, diurutkan dari timestamp terbaru."""
        query = "SELECT * FROM inspections ORDER BY timestamp DESC"
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                # Cast timestamp format string for consistent output with SQLite
                for r in rows:
                    if isinstance(r.get("timestamp"), datetime):
                        r["timestamp"] = r["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                return rows
        except Exception as e:
            print(f"[MYSQL DB ERROR] Gagal mengambil data inspeksi: {e}")
            return []
        finally:
            conn.close()

    def get_inspection_by_id(self, inspection_id: int) -> dict:
        """Ambil satu data inspeksi berdasarkan ID."""
        query = "SELECT * FROM inspections WHERE id = %s"
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (inspection_id,))
                row = cursor.fetchone()
                if row and isinstance(row.get("timestamp"), datetime):
                    row["timestamp"] = row["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                return row
        except Exception as e:
            print(f"[MYSQL DB ERROR] Gagal mengambil inspeksi ID {inspection_id}: {e}")
            return None
        finally:
            conn.close()

    def delete_inspection(self, inspection_id: int):
        """Hapus satu data inspeksi berdasarkan ID."""
        query = "DELETE FROM inspections WHERE id = %s"
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (inspection_id,))
        except Exception as e:
            print(f"[MYSQL DB ERROR] Gagal menghapus inspeksi ID {inspection_id}: {e}")
            raise
        finally:
            conn.close()

    def delete_multiple(self, ids: list):
        """Hapus beberapa data inspeksi sekaligus berdasarkan list ID."""
        if not ids:
            return

        placeholders = ", ".join(["%s"] * len(ids))
        query = f"DELETE FROM inspections WHERE id IN ({placeholders})"

        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, ids)
        except Exception as e:
            print(f"[MYSQL DB ERROR] Gagal menghapus {len(ids)} inspeksi: {e}")
            raise
        finally:
            conn.close()

    def mark_uploaded(self, inspection_id: int):
        """Tandai inspeksi sebagai sudah diupload (uploaded = 1)."""
        query = "UPDATE inspections SET uploaded = 1 WHERE id = %s"
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (inspection_id,))
        except Exception as e:
            print(f"[MYSQL DB ERROR] Gagal menandai upload ID {inspection_id}: {e}")
            raise
        finally:
            conn.close()

    def get_record_count(self) -> int:
        """Hitung total jumlah record inspeksi."""
        query = "SELECT COUNT(*) as total FROM inspections"
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query)
                row = cursor.fetchone()
                return row["total"] if row else 0
        except Exception as e:
            print(f"[MYSQL DB ERROR] Gagal menghitung record: {e}")
            return 0
        finally:
            conn.close()

    def get_pending_count(self) -> int:
        """Hitung jumlah record yang belum diupload (uploaded = 0)."""
        query = "SELECT COUNT(*) as total FROM inspections WHERE uploaded = 0"
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query)
                row = cursor.fetchone()
                return row["total"] if row else 0
        except Exception as e:
            print(f"[MYSQL DB ERROR] Gagal menghitung pending: {e}")
            return 0
        finally:
            conn.close()

    def __repr__(self) -> str:
        return f"MySQLDatabaseHandler(host='{self.config['host']}', db='{self.config['database']}')"
