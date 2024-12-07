import subprocess
import time
import threading
import logging
import psutil

class StreamManager:
    def __init__(self, url1, url2=None, image_path=None, youtube_url1=None, youtube_key1=None, youtube_url2=None, youtube_key2=None):
        self.url1 = url1
        self.url2 = url2
        self.image_path = image_path
        self.youtube_url1 = youtube_url1
        self.youtube_key1 = youtube_key1
        self.youtube_url2 = youtube_url2
        self.youtube_key2 = youtube_key2
        self.lock = threading.Lock()
        self.ffplay_processes = []

    def is_stream_active(self, url):
        try:
            result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type', '-of', 'default=noprint_wrappers=1:nokey=1', url], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            return result.stdout != b''
        except subprocess.TimeoutExpired:
            logging.error(f"Timeout expired while checking stream: {url}")
            return False
        except Exception as e:
            logging.error(f"Error checking stream {url}: {e}")
            return False

    def play_stream(self, url, x, y, width, height):
        command = [
            'ffplay', '-vcodec', 'h264_v4l2m2m', '-x', str(width), '-y', str(height), '-left', str(x), '-top', str(y), '-noborder', '-loglevel', 'quiet', '-sync', 'ext', url
        ]
        with self.lock:
            ffplay_process = subprocess.Popen(command)
            self.ffplay_processes.append(ffplay_process)
        try:
            ffplay_process.communicate()
        except Exception as e:
            logging.error(f"Error playing stream {url}: {e}")
        finally:
            ffplay_process.terminate()
            ffplay_process.wait()

    def stream_to_youtube(self, input_url, youtube_url, youtube_key):
        command = [
            'ffmpeg', '-re', '-i', input_url, '-c:v', 'libx264', '-preset', 'veryfast', '-maxrate', '3000k', '-bufsize', '6000k', '-pix_fmt', 'yuv420p', '-g', '50', '-c:a', 'aac', '-b:a', '160k', '-ar', '44100', '-f', 'flv', f'{youtube_url}/{youtube_key}'
        ]
        with self.lock:
            ffmpeg_process = subprocess.Popen(command)
            self.ffplay_processes.append(ffmpeg_process)
        try:
            ffmpeg_process.communicate()
        except Exception as e:
            logging.error(f"Error streaming to YouTube: {e}")
        finally:
            ffmpeg_process.terminate()
            ffmpeg_process.wait()

    def monitor_cpu_usage(self):
        while True:
            with self.lock:
                for process in self.ffplay_processes:
                    try:
                        p = psutil.Process(process.pid)
                        cpu_usage = p.cpu_percent(interval=1)
                        if cpu_usage < 5:  # Threshold for CPU usage
                            logging.warning(f"Low CPU usage detected for process {process.pid}. Restarting stream...")
                            process.terminate()
                            process.wait()
                            self.ffplay_processes.remove(process)
                    except psutil.NoSuchProcess:
                        self.ffplay_processes.remove(process)
            time.sleep(60)

    def start_stream(self):
        monitor_thread = threading.Thread(target=self.monitor_cpu_usage)
        monitor_thread.start()

        while True:
            if self.is_stream_active(self.url1):
                logging.info("Stream 1 is active. Starting ffplay...")
                
                play_thread1 = threading.Thread(target=self.play_stream, args=(self.url1, 0, 0, 1920, 1080))  # Left half of the screen
                play_thread1.start()

                if self.youtube_url1 and self.youtube_key1:
                    youtube_thread1 = threading.Thread(target=self.stream_to_youtube, args=(self.url1, self.youtube_url1, self.youtube_key1))
                    youtube_thread1.start()

                if self.url2 and self.is_stream_active(self.url2):
                    logging.info("Stream 2 is active. Starting ffplay...")
                    play_thread2 = threading.Thread(target=self.play_stream, args=(self.url2, 1920, 0, 1920, 1080))  # Right half of the screen
                    play_thread2.start()

                    if self.youtube_url2 and self.youtube_key2:
                        youtube_thread2 = threading.Thread(target=self.stream_to_youtube, args=(self.url2, self.youtube_url2, self.youtube_key2))
                        youtube_thread2.start()

                    play_thread2.join()

                play_thread1.join()

                logging.error("Stream disconnected. Restarting in 5 seconds...")
                time.sleep(60)
            else:
                logging.error("Stream 1 is not active. Checking again in 5 seconds...")
                time.sleep(5)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("stream_manager.log"),
            logging.StreamHandler()
        ]
    )
    stream_url1 = "rtmp://192.168.1.74/bcs/channel0_ext.bcs?channel=0&stream=0&user=admin&password=curling1"
    stream_url2 = None
    image_path = "/home/pi/rtmpautodisplay/placeholder.png"
    youtube_url1 = "rtmp://a.rtmp.youtube.com/live2"
    youtube_key1 = "YOUR_YOUTUBE_STREAM_KEY_1"
    youtube_url2 = None
    youtube_key2 = None
    
    time.sleep(5)
    stream_manager = StreamManager(stream_url1, stream_url2, image_path, youtube_url1, youtube_key1, youtube_url2, youtube_key2)
    stream_manager.start_stream()
