from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from ui.styles import get_button_style

class DataPage(QWidget):
    start_new_inspection = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = None
        self.api = None
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(24)
        
        header = QLabel("Data Inspeksi")
        header.setObjectName("title_label")
        main_layout.addWidget(header)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(16)
        
        self.btn_new = QPushButton("➕ Mulai Inspeksi Baru")
        self.btn_new.setStyleSheet(get_button_style('primary'))
        self.btn_new.setFixedHeight(52)
        self.btn_new.clicked.connect(self.start_new_inspection.emit)
        btn_layout.addWidget(self.btn_new)
        
        btn_layout.addStretch()
        
        self.btn_refresh = QPushButton("🔄 Refresh")
        self.btn_refresh.setStyleSheet(get_button_style('ghost'))
        self.btn_refresh.setFixedHeight(52)
        self.btn_refresh.clicked.connect(self.refresh_table)
        btn_layout.addWidget(self.btn_refresh)
        
        self.btn_upload_selected = QPushButton("📤 Upload Terpilih")
        self.btn_upload_selected.setStyleSheet(get_button_style('secondary'))
        self.btn_upload_selected.setFixedHeight(52)
        self.btn_upload_selected.clicked.connect(self.upload_selected)
        btn_layout.addWidget(self.btn_upload_selected)
        
        self.btn_delete_selected = QPushButton("🗑 Hapus Terpilih")
        self.btn_delete_selected.setStyleSheet(get_button_style('danger'))
        self.btn_delete_selected.setFixedHeight(52)
        self.btn_delete_selected.clicked.connect(self.delete_selected)
        btn_layout.addWidget(self.btn_delete_selected)
        
        self.btn_upload = QPushButton("📤 Upload Semua")
        self.btn_upload.setStyleSheet(get_button_style('warning'))
        self.btn_upload.setFixedHeight(52)
        self.btn_upload.clicked.connect(self.upload_all)
        btn_layout.addWidget(self.btn_upload)
        
        main_layout.addLayout(btn_layout)
        
        card_frame = QFrame()
        card_frame.setObjectName("card_frame")
        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(20, 20, 20, 20)
        
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Pilih", "ID", "Perusahaan", "Kebun", "Blok", "Tanggal", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.NoSelection) # Selection is done via checkboxes
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False) # Looks cleaner without full grid if using bottom borders
        card_layout.addWidget(self.table)
        
        main_layout.addWidget(card_frame, 1)

    def set_database(self, db):
        self.db = db

    def set_api_handler(self, api):
        self.api = api

    def refresh_table(self):
        if not self.db: return
        data = self.db.get_all_inspections()
        self.table.setRowCount(len(data))
        for r, row in enumerate(data):
            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk_item.setCheckState(Qt.Unchecked)
            self.table.setItem(r, 0, chk_item)
            
            self.table.setItem(r, 1, QTableWidgetItem(str(row.get('id', ''))))
            self.table.setItem(r, 2, QTableWidgetItem(row.get('nama_perusahaan', '')))
            self.table.setItem(r, 3, QTableWidgetItem(row.get('nama_kebun', '')))
            self.table.setItem(r, 4, QTableWidgetItem(row.get('no_blok', '')))
            self.table.setItem(r, 5, QTableWidgetItem(row.get('tanggal_pengambilan', '')))
            status = "✅ Uploaded" if row.get('uploaded', 0) else "⏳ Pending"
            self.table.setItem(r, 6, QTableWidgetItem(status))

    def delete_selected(self):
        if not self.db: return
        
        selected_ids = []
        for r in range(self.table.rowCount()):
            chk_item = self.table.item(r, 0)
            if chk_item and chk_item.checkState() == Qt.Checked:
                id_item = self.table.item(r, 1)
                if id_item:
                    selected_ids.append(int(id_item.text()))
                    
        if not selected_ids:
            QMessageBox.warning(self, "Tidak Ada Pilihan", "Silakan centang (checkbox) data di tabel yang ingin dihapus terlebih dahulu.")
            return
        
        reply = QMessageBox.question(
            self, 
            "Konfirmasi Hapus 🗑", 
            f"Apakah Anda yakin ingin menghapus {len(selected_ids)} data terpilih?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                for rid in selected_ids:
                    self.db.delete_inspection(rid)
                QMessageBox.information(self, "Sukses", f"{len(selected_ids)} data berhasil dihapus!")
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Gagal menghapus data: {e}")

    def upload_selected(self):
        if not self.db or not self.api: return
        
        selected_ids = []
        for r in range(self.table.rowCount()):
            chk_item = self.table.item(r, 0)
            if chk_item and chk_item.checkState() == Qt.Checked:
                id_item = self.table.item(r, 1)
                if id_item:
                    selected_ids.append(int(id_item.text()))
                    
        if not selected_ids:
            QMessageBox.warning(self, "Tidak Ada Pilihan", "Silakan centang (checkbox) data di tabel yang ingin di-upload terlebih dahulu.")
            return
        
        try:
            self.btn_upload_selected.setText("⏳ Mengunggah...")
            self.btn_upload_selected.setEnabled(False)
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()
            
            success_count = 0
            for record_id in selected_ids:
                row_data = self.db.get_inspection_by_id(record_id)
                if not row_data:
                    continue
                    
                photo_path = row_data.get('foto_path', None)
                upload_data = row_data.copy()
                if 'foto_path' in upload_data: del upload_data['foto_path']
                if 'uploaded' in upload_data: del upload_data['uploaded']
                
                result = self.api.upload_inspection(upload_data, photo_path)
                if result.get('success', False):
                    self.db.mark_uploaded(record_id)
                    success_count += 1
            
            self.btn_upload_selected.setText("📤 Upload Terpilih")
            self.btn_upload_selected.setEnabled(True)
            
            QMessageBox.information(self, "Upload Selesai", f"Berhasil mengunggah {success_count} dari {len(selected_ids)} data terpilih.")
            self.refresh_table()
                
                
        except Exception as e:
            self.btn_upload_selected.setText("📤 Upload Terpilih")
            self.btn_upload_selected.setEnabled(True)
            QMessageBox.critical(self, "Error", f"Terjadi kesalahan saat upload: {e}")

    def upload_all(self):
        if not self.db or not self.api: return
        try:
            data = self.db.get_all_inspections()
            pending_items = [row for row in data if not row.get('uploaded', 0)]
            
            if not pending_items:
                QMessageBox.information(self, "Info", "Semua data sudah ter-upload!")
                return
                
            reply = QMessageBox.question(
                self, 
                "Konfirmasi Upload 📤", 
                f"Terdapat {len(pending_items)} data pending. Apakah Anda yakin ingin mengunggah semuanya?",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
                
            self.btn_upload.setText("⏳ Mengunggah...")
            self.btn_upload.setEnabled(False)
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()
            
            success_count = 0
            for row in pending_items:
                record_id = row.get('id')
                photo_path = row.get('foto_path', None)
                
                upload_data = row.copy()
                if 'foto_path' in upload_data:
                    del upload_data['foto_path']
                if 'uploaded' in upload_data:
                    del upload_data['uploaded']
                    
                res = self.api.upload_inspection(upload_data, photo_path)
                if res.get('success', False):
                    self.db.mark_uploaded(record_id)
                    success_count += 1
            
            self.btn_upload.setText("📤 Upload Semua")
            self.btn_upload.setEnabled(True)
            
            QMessageBox.information(self, "Upload Selesai 🎉", f"Berhasil mengunggah {success_count} dari {len(pending_items)} data!")
            self.refresh_table()
            
        except Exception as e:
            self.btn_upload.setText("📤 Upload Semua")
            self.btn_upload.setEnabled(True)
            QMessageBox.critical(self, "Error", f"Terjadi kesalahan saat upload batch: {e}")
