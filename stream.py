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

    def show_image(self, image_path):
        for display in self.connected_displays:
            subprocess.Popen(['feh', '-F', '--on-top', '--auto-zoom', '--fullscreen', '--display', display, image_path])

class StreamManager:
    def __init__(self, url, image_path):
        self.url = url
        self.image_path = image_path
        self.display_manager = DisplayManager()
        self.ffplay_process = None
        self.lock = threading.Lock()

    def is_stream_active(self):
        try:
            result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type', '-of', 'default=noprint_wrappers=1:nokey=1', self.url], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            return result.stdout != b''
        except subprocess.TimeoutExpired:
            return False

    def detect_freezes(self):
        command = [
            'ffmpeg', '-i', self.url, '-vf', 'freezedetect=n=-60dB:d=2',
            '-map', '0:v:0', '-f', 'null', '-', '2>&1'
        ]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        
        while True:
            line = process.stdout.readline()
            if b'freeze_start' in line:
                logging.info("Freeze detected. Terminating ffplay process...")
                with self.lock:
                    if self.ffplay_process:
                        self.ffplay_process.terminate()
                        break

            if not self.is_stream_active():
                logging.info("Stream is not active. Terminating ffplay process...")
                with self.lock:
                    if self.ffplay_process:
                        self.ffplay_process.terminate()
                        break

            time.sleep(10)

    def play_stream(self):
        command = ['ffplay', '-fs', '-an', self.url]
        with self.lock:
            self.ffplay_process = subprocess.Popen(command)
        self.ffplay_process.communicate()

    def start_stream(self):
        while True:
            if self.is_stream_active():
                logging.info("Stream is active. Starting ffplay and freeze detection...")
                subprocess.run(['pkill', 'feh'])
                
                freeze_thread = threading.Thread(target=self.detect_freezes)
                play_thread = threading.Thread(target=self.play_stream)

                freeze_thread.start()
                play_thread.start()

                freeze_thread.join()
                play_thread.join()

                logging.info("Stream disconnected or freeze detected. Showing image and restarting in 5 seconds...")
                self.display_manager.show_image(self.image_path)
                time.sleep(5)
            else:
                logging.info("Stream is not active. Showing image and checking again in 5 seconds...")
                self.display_manager.show_image(self.image_path)
                time.sleep(5)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    stream_url = "rtmp://10.0.0.62/bcs/channel0_ext.bcs?channel=0&stream=0&user=admin&password=curling1"
    image_path = "/home/pi/rpisurv/surveillance/images/connecting.png"
    
    display_manager = DisplayManager()
    display_manager.show_image(image_path)
    time.sleep(5)
    stream_manager = StreamManager(stream_url, image_path)
    stream_manager.start_stream()
