import subprocess
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

class StreamManager:
    def __init__(self, url1, url2):
        self.url1 = url1
        self.url2 = url2
        self.display_manager = DisplayManager()

    def play_stream(self, url, display):
        command = [
            'cvlc', '--fullscreen', '--no-video-title-show', '--x11-display', display, url
        ]
        subprocess.Popen(command)

    def start_streams(self):
        if 'HDMI1' in self.display_manager.connected_displays and 'HDMI2' in self.display_manager.connected_displays:
            logging.info("Starting streams on HDMI1 and HDMI2...")
            self.play_stream(self.url1, ':0.0+HDMI1')
            self.play_stream(self.url2, ':0.0+HDMI2')
        else:
            logging.error("HDMI1 or HDMI2 not connected.")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("stream_manager.log"),
            logging.StreamHandler()
        ]
    )
    stream_url1 = "rtmp://10.0.0.62/bcs/channel0_ext.bcs?channel=0&stream=0&user=admin&password=curling1"
    stream_url2 = "rtmp://10.0.0.62/bcs/channel0_ext.bcs?channel=0&stream=0&user=admin&password=curling1"
    
    stream_manager = StreamManager(stream_url1, stream_url2)
    stream_manager.start_streams()
