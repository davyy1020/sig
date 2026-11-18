"""
Web Report Server & API Backend
===============================
Aplikasi Flask Web Report untuk menerima upload data inspeksi & foto
dari aplikasi client (Jetson/MiniPC) dan menyajikannya dalam dashboard web.
"""

import os
import sys
import json
from datetime import datetime
from werkzeug.utils import secure_filename

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from flask import Flask, render_template, request, jsonify, send_from_directory
from database.mysql_db_handler import MySQLDatabaseHandler, HAS_PYMYSQL
from database.db_handler import DatabaseHandler

app = Flask(__name__, static_folder="static", template_folder="templates")

# Konfigurasi Upload Directory
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads", "photos")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp"}

# Database Configuration
DB_TYPE = os.environ.get("DB_TYPE", "sqlite")
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "sig_monitoring")


def get_db():
    """Mendapatkan handler database yang aktif (MySQL dengan SQLite fallback)."""
    if DB_TYPE.lower() == "mysql" and HAS_PYMYSQL:
        try:
            return MySQLDatabaseHandler(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE,
                auto_create_db=True,
            )
        except Exception as e:
            print(f"[WEB REPORT DB WARNING] MySQL connection error: {e}. Fallback to SQLite.")

    return DatabaseHandler()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    """Halaman Utama Web Report Dashboard."""
    return render_template("report.html")


@app.route("/api/inspections", methods=["GET"])
def get_inspections():
    """API Endpoint untuk mengambil daftar seluruh inspeksi."""
    db = get_db()
    inspections = db.get_all_inspections()
    return jsonify({"success": True, "count": len(inspections), "data": inspections})


@app.route("/api/upload", methods=["POST"])
def upload_inspection():
    """
    API Endpoint untuk menerima upload data inspeksi + foto.
    Form Parameters:
    - json_data: JSON string data inspeksi
    - photo (opsional): File foto yang diupload
    """
    try:
        raw_json = request.form.get("json_data", "{}")
        data = json.loads(raw_json)

        # Proses Upload Foto (jika ada)
        photo_url = data.get("foto_path", "")
        if "photo" in request.files:
            file = request.files["photo"]
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                saved_filename = f"{timestamp_str}_{filename}"
                save_path = os.path.join(app.config["UPLOAD_FOLDER"], saved_filename)
                file.save(save_path)

                # Set relative photo URL untuk disajikan di web
                photo_url = f"/uploads/photos/{saved_filename}"
                data["foto_path"] = photo_url

        # Set status uploaded = 1 pada database server
        data["uploaded"] = 1

        db = get_db()
        inserted_id = db.insert_inspection(data)

        return jsonify({
            "success": True,
            "message": "Data inspeksi dan foto berhasil diterima di server!",
            "id": inserted_id,
            "foto_url": photo_url
        }), 201

    except Exception as e:
        print(f"[WEB REPORT ERROR] Gagal memproses upload: {e}")
        return jsonify({
            "success": False,
            "message": f"Server Error: {str(e)}"
        }), 500


@app.route("/uploads/photos/<filename>")
def serve_photo(filename):
    """Serve static uploaded photos for <img> tags in web browser."""
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[OK] Web Report Server running on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)

