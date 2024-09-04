import subprocess
import time
import threading
import logging
import yaml

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
            
            logging.info(f"Connected displays: {connected_displays}")
            return connected_displays
        except subprocess.CalledProcessError as e:
            logging.error(f"Error detecting connected displays: {e}")
            return []

    def show_image(self, image_path, display):
        subprocess.Popen(['feh', '-F', '--on-top', '--auto-zoom', '--fullscreen', '--display', display, image_path])

class StreamManager:
    def __init__(self, url, image_path, display):
        self.url = url
        self.image_path = image_path
        self.display = display
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
                logging.info(f"Freeze detected on {self.display}. Terminating ffplay process...")
                with self.lock:
                    if self.ffplay_process:
                        self.ffplay_process.terminate()
                        break

            if not self.is_stream_active():
                logging.info(f"Stream is not active on {self.display}. Terminating ffplay process...")
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
                logging.info(f"Stream is active on {self.display}. Starting ffplay and freeze detection...")
                subprocess.run(['pkill', 'feh'])
                
                freeze_thread = threading.Thread(target=self.detect_freezes)
                play_thread = threading.Thread(target=self.play_stream)

                freeze_thread.start()
                play_thread.start()

                freeze_thread.join()
                play_thread.join()

                logging.info(f"Stream disconnected or freeze detected on {self.display}. Showing image and restarting in 5 seconds...")
                self.display_manager.show_image(self.image_path, self.display)
                time.sleep(5)
            else:
                logging.info(f"Stream is not active on {self.display}. Showing image and checking again in 5 seconds...")
                self.display_manager.show_image(self.image_path, self.display)
                time.sleep(5)

def load_config(config_path):
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

if __name__ == "__main__":
    logging.basicConfig(filename='stream_manager.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    config = load_config('config.yaml')
    logging.info(f"Loaded config: {config}")
    
    display_manager = DisplayManager()
    
    for display, settings in config['streams'].items():
        if display in display_manager.connected_displays:
            display_manager.show_image(settings['image_path'], display)
        else:
            logging.warning(f"Display {display} not connected.")
    
    time.sleep(5)
    
    for display, settings in config['streams'].items():
        if display in display_manager.connected_displays:
            stream_manager = StreamManager(settings['url'], settings['image_path'], display)
            stream_manager_thread = threading.Thread(target=stream_manager.start_stream)
            stream_manager_thread.start()
        else:
            logging.warning(f"Skipping stream for {display} as it is not connected.")
