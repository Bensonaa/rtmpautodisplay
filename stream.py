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
        self.url2 = url2
        self.image_path = image_path
        self.display_manager = DisplayManager()
        self.ffplay_process1 = None
        self.ffplay_process2 = None
        self.lock = threading.Lock()

    def is_stream_active(self, url):
        try:
            result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type', '-of', 'default=noprint_wrappers=1:nokey=1', url], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            return result.stdout != b''
        except subprocess.TimeoutExpired:
            return False

    def detect_freezes(self, url, ffplay_process):
        command = [
            'ffmpeg', '-i', url, '-vf', 'freezedetect=n=-60dB:d=2',
            '-map', '0:v:0', '-f', 'null', '-', '2>&1'
        ]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        
        while True:
            line = process.stdout.readline()
            if b'freeze_start' in line:
                logging.info("Freeze detected. Terminating ffplay process...")
                with self.lock:
                    if ffplay_process:
                        ffplay_process.terminate()
                        break

            if not self.is_stream_active(url):
                logging.info("Stream is not active. Terminating ffplay process...")
                with self.lock:
                    if ffplay_process:
                        ffplay_process.terminate()
                        break

            time.sleep(10)

    def play_stream(self, url):
        command = ['ffplay', '-fs', '-an', url]
        with self.lock:
            ffplay_process = subprocess.Popen(command)
        ffplay_process.communicate()

    def start_stream(self):
        while True:
            if self.is_stream_active(self.url1) and self.is_stream_active(self.url2):
                logging.info("Streams are active. Starting ffplay and freeze detection...")
                subprocess.run(['pkill', 'feh'])
                
                freeze_thread1 = threading.Thread(target=self.detect_freezes, args=(self.url1, self.ffplay_process1))
                play_thread1 = threading.Thread(target=self.play_stream, args=(self.url1,))

                freeze_thread2 = threading.Thread(target=self.detect_freezes, args=(self.url2, self.ffplay_process2))
                play_thread2 = threading.Thread(target=self.play_stream, args=(self.url2,))

                freeze_thread1.start()
                play_thread1.start()

                freeze_thread2.start()
                play_thread2.start()

                freeze_thread1.join()
                play_thread1.join()

                freeze_thread2.join()
                play_thread2.join()

                logging.info("Stream disconnected or freeze detected. Showing image and restarting in 5 seconds...")
                self.display_manager.show_image('HDMI1', self.image_path)
                self.display_manager.show_image('HDMI2', self.image_path)
                time.sleep(5)
            else:
                logging.info("Streams are not active. Showing image and checking again in 5 seconds...")
                self.display_manager.show_image('HDMI1', self.image_path)
                self.display_manager.show_image('HDMI2', self.image_path)
                time.sleep(5)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    stream_url1 = "rtmp://10.0.0.62/bcs/channel0_ext.bcs?channel=0&stream=0&user=admin&password=curling1"
    stream_url2 = "rtmp://10.0.0.62/bcs/channel0_ext.bcs?channel=0&stream=0&user=admin&password=curling1"
    image_path = "/home/pi/rtmpautodisplay/placeholder.png"
    
    display_manager = DisplayManager()
    display_manager.show_image('HDMI1', image_path)
    display_manager.show_image('HDMI2', image_path)
    time.sleep(5)
    stream_manager = StreamManager(stream_url1, stream_url2, image_path)
    stream_manager.start_stream()
