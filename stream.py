import subprocess
import time
import os

class DisplayManager:
    def __init__(self):
        self.connected_displays = self.get_connected_displays()

    def get_connected_displays(self):
        try:
            result = subprocess.run(['xrandr'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = result.stdout.decode()
            connected_displays = []
            
            for line in output.split('\n'):
                if ' connected' in line:
                    display = line.split()[0]
                    connected_displays.append(display)
            
            return connected_displays
        except Exception as e:
            print(f"Error detecting connected displays: {e}")
            return []

    def show_image(self, image_path):
        for display in self.connected_displays:
            subprocess.Popen(['feh', '-F', '--on-top', '--auto-zoom', '--fullscreen', '--display', display, image_path])

class StreamManager:
    def __init__(self, url, image_path):
        self.url = url
        self.image_path = image_path
        self.display_manager = DisplayManager()

    def is_stream_active(self):
        try:
            result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type', '-of', 'default=noprint_wrappers=1:nokey=1', self.url], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            return result.stdout != b''
        except subprocess.TimeoutExpired:
            return False

    def start_stream(self):
        while True:
            if self.is_stream_active():
                print("Stream is active. Starting ffplay...")
                subprocess.run(['pkill', 'feh'])
                
                processes = []
                for display in self.display_manager.connected_displays:
                    process = subprocess.Popen(['ffplay', '-fs', '-an', '-vcodec', 'h264_v4l2m2m', '-i', self.url])
                    processes.append(process)
                
                for process in processes:
                    process.wait()
                
                print("Stream disconnected. Showing image and restarting in 5 seconds...")
                self.display_manager.show_image(self.image_path)
                time.sleep(5)
            else:
                print("Stream is not active. Showing image and checking again in 5 seconds...")
                self.display_manager.show_image(self.image_path)
                time.sleep(5)

if __name__ == "__main__":
    stream_url = "rtmp://10.0.0.62/bcs/channel0_ext.bcs?channel=0&stream=0&user=admin&password=curling1"
    image_path = "/home/pi/rpisurv/surveillance/images/connecting.png"
    
    display_manager = DisplayManager()
    display_manager.show_image(image_path)
    time.sleep(5)
    
    stream_manager = StreamManager(stream_url, image_path)
    stream_manager.start_stream()
