"""
Setup MySQL Helper & Tester
===========================
Script bantuan untuk menguji koneksi server MySQL, membuat database, 
dan membuat tabel 'inspections'.

Penggunaan CLI:
    python database/setup_mysql.py --host localhost --user root --password mysecret
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.mysql_db_handler import MySQLDatabaseHandler, HAS_PYMYSQL


def setup_mysql(
    host="localhost",
    port=3306,
    user="root",
    password="",
    database="sig_monitoring",
):
    """Fungsi helper untuk inisialisasi dan pengujian database MySQL."""
    print("=" * 60)
    print("🛠 SETUP & UJI KONEKSI DATABASE MYSQL")
    print("=" * 60)

    if not HAS_PYMYSQL:
        print("❌ ERROR: Module 'pymysql' belum terinstall!")
        print("💡 Silakan jalankan: pip install pymysql")
        return False

    print(f"📡 Mencoba terhubung ke MySQL Server:")
    print(f"   Host     : {host}:{port}")
    print(f"   User     : {user}")
    print(f"   Database : {database}")

    try:
        handler = MySQLDatabaseHandler(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            auto_create_db=True,
        )
        print("✅ Berhasil terhubung ke server MySQL!")
        print(f"✅ Database '{database}' dan tabel 'inspections' siap digunakan.")

        record_count = handler.get_record_count()
        pending_count = handler.get_pending_count()
        print(f"📊 Total Data Inspeksi : {record_count}")
        print(f"⏳ Data Belum Upload   : {pending_count}")
        print("=" * 60)
        return True
    except Exception as e:
        print(f"❌ GAGAL TERHUBUNG KE MYSQL: {e}")
        print("=" * 60)
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup Database MySQL untuk SIG Monitoring")
    parser.add_argument("--host", default="localhost", help="MySQL Server host (default: localhost)")
    parser.add_argument("--port", type=int, default=3306, help="MySQL Server port (default: 3306)")
    parser.add_argument("--user", default="root", help="MySQL Server username (default: root)")
    parser.add_argument("--password", default="", help="MySQL Server password (default: '')")
    parser.add_argument("--database", default="sig_monitoring", help="MySQL database name (default: sig_monitoring)")

    args = parser.parse_args()
    success = setup_mysql(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database,
    )
    sys.exit(0 if success else 1)
