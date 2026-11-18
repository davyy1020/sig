"""
API Handler - Modul upload data inspeksi ke server
===================================================
Menangani pengiriman data inspeksi perkebunan dan foto
ke server API menggunakan HTTP POST.

Default endpoint menggunakan httpbin.org untuk pengujian.
"""

import requests
import json
import os
from datetime import datetime


class APIHandler:
    """
    Handler untuk upload data inspeksi ke REST API.
    
    Fitur:
    - Upload data inspeksi + foto ke server
    - Test koneksi ke server
    - Batch upload beberapa inspeksi sekaligus
    - Penanganan error dan timeout yang komprehensif
    
    Penggunaan:
        api = APIHandler(base_url='https://httpbin.org')
        
        # Test koneksi
        if api.test_connection():
            result = api.upload_inspection(data, photo_path='foto.jpg')
            print(result)
    """

    def __init__(self, base_url: str = "https://httpbin.org"):
        """
        Inisialisasi APIHandler.

        Args:
            base_url: URL dasar API server (tanpa trailing slash).
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = 30  # Timeout dalam detik

    def upload_inspection(self, data: dict, photo_path: str = None) -> dict:
        """
        Upload satu data inspeksi ke server.

        Data dikirim sebagai multipart form:
        - 'json_data': String JSON berisi data inspeksi
        - 'photo': File foto (jika tersedia)

        Args:
            data: Dictionary berisi data inspeksi.
            photo_path: Path ke file foto (opsional).

        Returns:
            Dictionary hasil upload:
            {
                'success': bool,
                'message': str,
                'response': dict atau None
            }
        """
        if "/api/upload" in self.base_url or "/post" in self.base_url:
            url = self.base_url
        else:
            url = f"{self.base_url}/api/upload"

        try:
            # Siapkan data form
            files = {}
            form_data = {
                "json_data": json.dumps(data, ensure_ascii=False, default=str)
            }

            # Cek photo_path dari argumen atau dari dictionary data
            if not photo_path:
                photo_path = data.get("foto_path", "")


            # Tambahkan file foto jika ada dan valid (bisa berupa semicolon-separated paths)
            if photo_path:
                paths = photo_path.split(";")
                valid_photo_path = None
                for p in paths:
                    p = p.strip()
                    if p and os.path.isfile(p):
                        valid_photo_path = p
                        break
                
                if valid_photo_path:
                    filename = os.path.basename(valid_photo_path)
                    files["photo"] = (
                        filename,
                        open(valid_photo_path, "rb"),
                        "image/jpeg",
                    )

            # Kirim request POST
            response = requests.post(
                url,
                data=form_data,
                files=files if files else None,
                timeout=self.timeout,
            )

            # Tutup file handle jika dibuka
            if "photo" in files:
                files["photo"][1].close()

            # Cek response status
            response.raise_for_status()

            return {
                "success": True,
                "message": f"Upload berhasil (HTTP {response.status_code})",
                "response": response.json(),
            }

        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": "Gagal terhubung ke server. Periksa koneksi internet.",
                "response": None,
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": f"Request timeout ({self.timeout} detik). Server tidak merespons.",
                "response": None,
            }
        except requests.exceptions.HTTPError as e:
            return {
                "success": False,
                "message": f"HTTP Error: {e}",
                "response": None,
            }
        except json.JSONDecodeError:
            return {
                "success": False,
                "message": "Response dari server bukan format JSON yang valid.",
                "response": None,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error tidak terduga: {str(e)}",
                "response": None,
            }

    def test_connection(self) -> bool:
        """
        Test koneksi ke server API.

        Mengirim GET request ke endpoint /get untuk memverifikasi
        bahwa server bisa dijangkau dan merespons.

        Returns:
            True jika server merespons dengan status 200, False jika tidak.
        """
        url = f"{self.base_url}/get"

        try:
            response = requests.get(url, timeout=self.timeout)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def upload_batch(self, items: list) -> list:
        """
        Upload beberapa data inspeksi secara berurutan.

        Args:
            items: List berisi dictionary dengan format:
                [
                    {'data': dict, 'photo_path': str atau None},
                    ...
                ]

        Returns:
            List hasil upload untuk setiap item:
            [
                {
                    'index': int,
                    'success': bool,
                    'message': str,
                    'response': dict atau None
                },
                ...
            ]
        """
        results = []

        for index, item in enumerate(items):
            data = item.get("data", {})
            photo_path = item.get("photo_path", None)

            # Upload setiap item
            result = self.upload_inspection(data, photo_path)

            # Tambahkan index untuk tracking
            result["index"] = index
            results.append(result)

        return results

    def __repr__(self) -> str:
        return f"APIHandler(base_url='{self.base_url}', timeout={self.timeout})"
