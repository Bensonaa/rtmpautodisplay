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
                    
            return connected_displays
        except subprocess.CalledProcessError as e:
            logging.error(f"Error detecting connected displays: {e}")
            return []
        
    def show_image(self, display, image_path):
        subprocess.Popen(['feh', '-F', '--auto-zoom', '--fullscreen', '--display', display, image_path])
        
class StreamManager:
    def __init__(self, url1, url2, image_path):
        self.url1 = url1
        self.url2 = url2 if url2 else None
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
        
    def play_stream(self, url):
        command = ['cvlc', '--fullscreen', '--no-audio', url]
        with self.lock:
            vlc_process = subprocess.Popen(command)
        vlc_process.communicate()
        
    def start_stream(self):
        while True:
            if self.is_stream_active(self.url1):
                logging.info("Stream 1 is active. Starting VLC...")
                subprocess.run(['pkill', 'feh'])
                play_thread1 = threading.Thread(target=self.play_stream, args=(self.url1,))
                play_thread1.start()
                play_thread1.join()
            else:
                logging.info("Stream 1 is not active. Showing image and checking again in 5 seconds...")
                self.display_manager.show_image('HDMI1', self.image_path)
                time.sleep(5)
                
            if self.url2 and self.is_stream_active(self.url2):
                logging.info("Stream 2 is active. Starting VLC...")
                play_thread2 = threading.Thread(target=self.play_stream, args=(self.url2,))
                play_thread2.start()
                play_thread2.join()
            elif self.url2:
                logging.info("Stream 2 is not active. Showing image and checking again in 5 seconds...")
                self.display_manager.show_image('HDMI2', self.image_path)
                time.sleep(5)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    stream_url1 = "rtmp://192.168.1.77/bcs/channel0_ext.bcs?channel=0&stream=0&user=admin&password=curling1"
    stream_url2 = None  # Replace with the second URL if available
    image_path = "/home/pi/rtmpautodisplay/placeholder.png"
    
    display_manager = DisplayManager()
    display_manager.show_image('HDMI1', image_path)
    display_manager.show_image('HDMI2', image_path)
    time.sleep(5)
    stream_manager = StreamManager(stream_url1, stream_url2, image_path)
    stream_manager.start_stream()
