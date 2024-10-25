import subprocess
import time
import threading
import logging

class DisplayManager:
    def __init__(self):
        self.connected_displays = self.get_connected_displays()

    def get_connected_displays(self):
        try:
            result = subprocess.run(['xrandr'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            output = result.stdout.decode()
            connected_displays = []
            
            for line in output.split('\n'):
                if ' connected' in line:
                    display = line.split()[0]
                    connected_displays.append(display)
            
            logging.info(f"Found displays: {connected_displays}")
            return connected_displays
        except subprocess.CalledProcessError as e:
            logging.error(f"Error detecting connected displays: {e}")
            return []

    def show_image(self, image_path, x, y, width, height):
        command = [
            'feh', '--fullscreen', '--auto-zoom', '--geometry', f'{width}x{height}+{x}+{y}', image_path
        ]
        subprocess.run(command)

class StreamManager:
    def __init__(self, url1, url2, image_path):
        self.url1 = url1
        self.url2 = url2
        self.image_path = image_path
        self.display_manager = DisplayManager()
        self.vlc_process1 = None
        self.vlc_process2 = None
        self.lock = threading.Lock()

    def is_stream_active(self, url):
        try:
            result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type', '-of', 'default=noprint_wrappers=1:nokey=1', url], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            return result.stdout != b''
        except subprocess.TimeoutExpired:
            return False

    def play_stream(self, url, x, y, width, height):
        command = [
            'cvlc', '--fullscreen', '--no-audio', url,
            '--width', str(width), '--height', str(height),
            '--video-x', str(x), '--video-y', str(y),
            '--network-caching=300', '--clock-jitter=0', '--clock-synchro=0'
        ]
        with self.lock:
            vlc_process = subprocess.Popen(command)
        vlc_process.communicate()

    def start_stream(self):
        while True:
            if self.is_stream_active(self.url1) and self.is_stream_active(self.url2):
                logging.info("Streams are active. Starting VLC...")
                subprocess.run(['pkill', 'feh'])
                
                play_thread1 = threading.Thread(target=self.play_stream, args=(self.url1, 0, 0, 1920, 1080))  # Left half of the screen
                play_thread2 = threading.Thread(target=self.play_stream, args=(self.url2, 1920, 0, 1920, 1080))  # Right half of the screen

                play_thread1.start()
                play_thread2.start()

                play_thread1.join()
                play_thread2.join()

                logging.error("Stream disconnected. Showing image and restarting in 5 seconds...")
                self.display_manager.show_image(self.image_path, 0, 0, 1920, 1080)
                self.display_manager.show_image(self.image_path, 1920, 0, 1920, 1080)
                time.sleep(5)
            else:
                logging.error("Streams are not active. Showing image and checking again in 5 seconds...")
                self.display_manager.show_image(self.image_path, 0, 0, 1920, 1080)
                self.display_manager.show_image(self.image_path, 1920, 0, 1920, 1080)
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
    stream_url1 = "rtmp://192.168.1.77/bcs/channel0_ext.bcs?channel=0&stream=0&user=admin&password=curling1"
    stream_url2 = "rtmp://192.168.1.72/bcs/channel0_ext.bcs?channel=0&stream=0&user=admin&password=curling1"
    image_path = "/home/pi/rtmpautodisplay/placeholder.png"
    
    display_manager = DisplayManager()
    display_manager.show_image(image_path, 0, 0, 1920, 1080)
    display_manager.show_image(image_path, 1920, 0, 1920, 1080)
    time.sleep(5)
    stream_manager = StreamManager(stream_url1, stream_url2, image_path)
    stream_manager.start_stream()
