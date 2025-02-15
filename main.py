import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                            QLineEdit, QLabel, QProgressBar, QCheckBox, QComboBox,
                            QHBoxLayout, QFrame, QSizePolicy, QScrollArea, QTabWidget,
                            QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon
from downloader import YouTubeDownloader
from pytube import Playlist


class ModernProgressBar(QProgressBar):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QProgressBar {
                border: 2px solid #2ecc71;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #2ecc71;
                border-radius: 3px;
            }
        """)

class DownloaderThread(QThread):
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    download_finished = pyqtSignal(bool, str, str, int)  # Include total_videos
    
    def __init__(self, url, format_type, is_playlist, prefix_index, progress_callback, status_callback, output_dir, total_videos=1):
        super().__init__()
        self.url = url
        self.format_type = format_type
        self.is_playlist = is_playlist
        self.prefix_index = prefix_index
        self.progress_callback = lambda p: self.progress_updated.emit(p)  # Convert callback to signal
        self.status_callback = lambda s: self.status_updated.emit(s)  # Convert callback to signal
        self.total_videos = total_videos  # Initialize total_videos
        self.playlist_title = ""  # Initialize playlist title
        self.output_dir = output_dir  # Store output directory
    
    def run(self):
        try:
            pl = Playlist(self.url)
            self.playlist_title = pl.title
            self.total_videos = pl.length if pl.length > 0 else 1
            playlist_dir = os.path.join(self.output_dir, self.playlist_title)
            os.makedirs(playlist_dir, exist_ok=True)  # Ensure directory exists
        except Exception as e:
            print(f"Error fetching playlist details: {e}")
            self.playlist_title = "قائمة تشغيل"
            self.total_videos = 1
            playlist_dir = os.path.join(self.output_dir, self.playlist_title)
            os.makedirs(playlist_dir, exist_ok=True)

        downloader = YouTubeDownloader(
            output_dir=playlist_dir,  # Use the playlist directory
            prefix_index=self.prefix_index,
            progress_callback=self.progress_callback,
            status_callback=self.status_callback,
            total_videos=self.total_videos,
            playlist_title=self.playlist_title
        )
        
        success, output_dir, total_videos, playlist_title = downloader.download(
            self.url, self.format_type, is_playlist=self.is_playlist
        )
        
        self.total_videos = total_videos
        self.playlist_title = playlist_title
        self.download_finished.emit(success, output_dir, self.playlist_title, self.total_videos)



class YouTubeDownloaderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.current_video_index = 0
        self.total_videos = 0
        self.downloader_thread = None
        self.playlist_title_label = QLabel("")  # Label for playlist title
        self.output_dir = "downloads"  # Default output directory
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("برنامج تحميل الفيديوهات من اليوتيوب")  # Improved Arabic title
        self.setWindowIcon(QIcon("path/to/icon.png"))  # Set the app icon
        self.setGeometry(100, 100, 600, 500)
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f6fa;
                color: #2f3640;
                font-size: 14px;
            }
            QLineEdit {
                padding: 8px;
                border: 2px solid #dcdde1;
                border-radius: 5px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #2ecc71;
            }
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:pressed {
                background-color: #219a52;
            }
            QComboBox {
                padding: 8px;
                border: 2px solid #dcdde1;
                border-radius: 5px;
                background-color: white;
            }
            QComboBox::drop-down {
                border: none;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QTabWidget::pane {
                border: 1px solid #dcdde1;
                border-radius: 5px;
            }
            QTabBar::tab {
                background: #2ecc71;
                color: white;
                padding: 10px;
                border: 1px solid #dcdde1;
                border-radius: 5px;
                width: 50%;  # Make tabbed buttons fill half the width
            }
            QTabBar::tab:selected {
                background: #27ae60;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # URL Section
        url_frame = QFrame()
        url_layout = QVBoxLayout()
        
        header_label = QLabel("برنامج تحميل قوائم التشغيل والفيديوهات والصوتيات")  # Improved Arabic title
        header_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2f3640;")
        url_layout.addWidget(header_label)
        
        self.url_label = QLabel("أدخل رابط يوتيوب أو قائمة التشغيل:")  # Arabic translation
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        url_layout.addWidget(self.url_label)
        url_layout.addWidget(self.url_input)
        
        url_frame.setLayout(url_layout)
        main_layout.addWidget(url_frame)

        # Format Selection using Tab Widget
        format_tab_widget = QTabWidget()
        self.audio_tab = QWidget()
        self.video_tab = QWidget()
        
        format_tab_widget.addTab(self.audio_tab, "صوت (MP3)")  # Arabic translation
        format_tab_widget.addTab(self.video_tab, "فيديو (MP4)")  # Arabic translation
        
        format_layout = QVBoxLayout()
        format_layout.addWidget(format_tab_widget)
        main_layout.addLayout(format_layout)

        # Checkboxes
        checkbox_frame = QFrame()
        checkbox_layout = QVBoxLayout()
        checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignRight)  # Align the entire layout to right
        
        prefix_layout = QHBoxLayout()
        prefix_layout.setSpacing(2)
        prefix_label = QLabel("إضافة رقم قبل العنوان")
        self.prefix_checkbox = QCheckBox()
        prefix_layout.addWidget(self.prefix_checkbox)
        prefix_layout.addWidget(prefix_label)
        
        
        checkbox_layout.addLayout(prefix_layout)
        checkbox_frame.setLayout(checkbox_layout)
        main_layout.addWidget(checkbox_frame)

        # Progress Section
        progress_frame = QFrame()
        progress_layout = QVBoxLayout()
        
        # Playlist Title and Count
        self.playlist_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.playlist_title_label)
        
        # Status label with improved styling
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 5px;
                border: 1px solid #dcdde1;
                min-height: 30px;
            }
        """)
        progress_layout.addWidget(self.status_label)
        
        progress_frame.setLayout(progress_layout)
        main_layout.addWidget(progress_frame)

        # Status Section
        status_frame = QFrame()
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.status_label)
        
        self.download_button = QPushButton("تحميل")  # Arabic translation
        self.download_button.setFixedHeight(40)
        self.download_button.setStyleSheet("background-color: #2ecc71; color: white;")  # Ensure button is filled with color
        self.download_button.clicked.connect(self.start_download)
        status_layout.addWidget(self.download_button)
        
        status_frame.setLayout(status_layout)
        main_layout.addWidget(status_frame)

        self.setLayout(main_layout)

    def update_overall_progress(self, video_progress):
        # This method can stay empty or be removed since we're not using progress bar
        pass

    def update_status_label(self, message):
        self.status_label.setText(message)

    def set_total_videos(self, playlist_title, total_videos):
        self.total_videos = total_videos
        self.playlist_title = playlist_title
        self.playlist_title_label.setText(f"قائمة التشغيل: {self.playlist_title}\nعدد الفيديوهات: {self.total_videos}")

    def start_download(self):
        if self.downloader_thread and self.downloader_thread.isRunning():
            return

        url = self.url_input.text()
        format_type = "bestaudio/best" if self.audio_tab.isVisible() else "bestvideo+bestaudio/best"
        prefix_index = self.prefix_checkbox.isChecked()
        
        if not url:
            self.status_label.setText("يرجى إدخال رابط صالح")
            return

        self.download_button.setEnabled(False)
        self.status_label.setText("جارٍ بدء التحميل...")
        self.playlist_title_label.clear()  # Clear the playlist title label
        self.status_label.clear()  # Clear the status label
        self.current_video_index = 0
        # Remove progress bar reset
        # self.overall_progress_bar.setValue(0)
        
        is_playlist = False
        
        # Pass callbacks directly to the thread
        self.downloader_thread = DownloaderThread(
            url, 
            format_type, 
            is_playlist, 
            prefix_index,
            self.update_overall_progress,
            self.update_status_label,
            self.output_dir,  # Pass output_dir
            total_videos=1
        )
        
        self.downloader_thread.progress_updated.connect(self.update_overall_progress)
        self.downloader_thread.status_updated.connect(self.update_status_label)
        self.downloader_thread.download_finished.connect(self.on_download_finished)
        self.downloader_thread.start()

    def on_download_finished(self, success, output_dir, playlist_title, total_videos):
        self.playlist_title = playlist_title
        self.set_total_videos(playlist_title, total_videos)
        if success:
            self.status_label.setText("اكتمل التحميل بنجاح!")
            try:
                os.startfile(output_dir)
            except Exception as e:
                print(f"Error opening folder: {e}")
        else:
            self.status_label.setText("حدث خطأ أثناء التحميل.")
        
        self.download_button.setEnabled(True)
        self.url_input.clear()  # Clear the text field after download

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern looking style
    window = YouTubeDownloaderApp()
    window.show()
    sys.exit(app.exec())