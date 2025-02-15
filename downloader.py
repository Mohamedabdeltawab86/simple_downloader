import os
import yt_dlp
import shutil
from PyQt6.QtWidgets import QProgressBar


class YouTubeDownloader:
    def __init__(self, output_dir, prefix_index=False, progress_callback=None, status_callback=None, total_videos=1, playlist_title="قائمة تشغيل"):
        self.base_dir = os.path.abspath(output_dir)  # Make path absolute
        self.output_dir = self.base_dir  # Initialize output_dir
        self.prefix_index = prefix_index
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self.current_video_index = 0
        self.total_videos = total_videos  # Initialize total_videos
        self.playlist_title = playlist_title  # Initialize playlist_title
        os.makedirs(self.base_dir, exist_ok=True)

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                total_bytes = d.get('total_bytes', d.get('total_bytes_estimate', 0))
                downloaded_bytes = d.get('downloaded_bytes', 0)
                
                if total_bytes > 0:
                    progress = int((downloaded_bytes / total_bytes) * 100)
                    if self.progress_callback:
                        self.progress_callback(progress)
                    
                    if self.status_callback:
                        speed = d.get('speed', 0)
                        if speed:
                            speed_mb = speed / 1024 / 1024
                            self.status_callback(
                                f"جارٍ تحميل الفيديو {self.current_video_index + 1} من {self.total_videos}"
                                f" ({speed_mb:.1f} MB/s)"
                            )
            except Exception as e:
                print(f"Error in progress_hook: {e}")
                
        elif d['status'] == 'finished':
            self.current_video_index += 1
            if self.progress_callback:
                self.progress_callback(0)  # Reset progress for next video

    def export_to_playlist_folder(self, source_dir):
        """
        Export downloaded videos to a new folder named after the playlist.
        Returns the path to the new folder.
        """
        try:
            # Create the export folder path
            export_folder = os.path.join(self.base_dir, "Playlists", self.sanitize_filename(self.playlist_title))
            os.makedirs(export_folder, exist_ok=True)

            # Move all video files from source directory to export folder
            for filename in os.listdir(source_dir):
                source_file = os.path.join(source_dir, filename)
                if os.path.isfile(source_file):
                    destination_file = os.path.join(export_folder, filename)
                    shutil.move(source_file, destination_file)

            if self.status_callback:
                self.status_callback(f"تم نقل الملفات إلى مجلد القائمة: {self.playlist_title}")

            return export_folder
        except Exception as e:
            print(f"Error exporting files: {e}")
            if self.status_callback:
                self.status_callback(f"خطأ في نقل الملفات: {str(e)}")
            return None

    def download(self, url, format_type, is_playlist=False):
        try:
            self.current_video_index = 0
            
            # Download options
            ydl_opts = {
                'format': format_type,
                'progress_hooks': [self.progress_hook],
                'outtmpl': os.path.join(self.output_dir, '%(playlist_index)03d-%(title)s.%(ext)s' if is_playlist else '%(title)s.%(ext)s'),
                'ignoreerrors': True,
                'no_warnings': True,
                'quiet': True,
                'extract_flat': False,
                'writethumbnail': False,
                'writeinfojson': False,
                'write_description': False,
                'write_annotations': False,
                'logger': None,
                'retries': 3,
                'fragment_retries': 3,
                'skip_download': False,
                'force_overwrites': True,
                'continue_dl': True,
                'noprogress': False,
                'logtostderr': False,
                'consoletitle': False,
                'prefer_ffmpeg': False,
                'hls_prefer_native': True,
                'no_playlist': not is_playlist,
            }

            if self.status_callback:
                self.status_callback(f"جارٍ التحميل... {self.current_video_index + 1} من {self.total_videos}")

            error = False
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    ydl.download([url])
                except Exception as e:
                    print(f"Download error: {e}")
                    if self.status_callback:
                        self.status_callback(f"حدث خطأ: {str(e)}")
                    error = True

            return not error, self.output_dir, self.total_videos, self.playlist_title
                
        except Exception as e:
            print(f"Error downloading: {e}")
            if self.status_callback:
                self.status_callback(f"حدث خطأ: {str(e)}")
            return False, self.output_dir, self.total_videos, self.playlist_title

    def sanitize_filename(self, name):
        return "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()