import subprocess
import time
import os

def is_connectable(url):
    try:
        ffprobeoutput = subprocess.run(['ffprobe', '-v', 'error', '-i', url, '-show_entries', 'stream=codec_type', '-of', 'default=noprint_wrappers=1:nokey=1'], timeout=10, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if ffprobeoutput.returncode == 0:
            return True
        else:
            return False
    except subprocess.TimeoutExpired as e:
        #logger.error(f"CameraStream: {self.name} {self.obfuscated_credentials_url} Not Connectable (ffprobe timed out, try increasing probe_timeout for this stream), configured timeout: {self.probe_timeout}")
        return False
    except Exception as e:
        #logger.error(f"CameraStream: {self.name} {self.obfuscated_credentials_url} Not Connectable ({erroroutput_newlinesremoved}), configured timeout: {self.probe_timeout}")
        return False

def show_image(image_path):
    # Display the image using feh in fullscreen mode
    subprocess.Popen(['feh', '-F', image_path])

def start_stream(url, image_path):
    while True:
        if is_connectable(url):
            print("Stream is active. Starting ffplay...")
            # Kill any existing feh processes
            subprocess.run(['pkill', 'feh'])
            
            # Start the ffplay process with fullscreen, no audio, and minimal latency
            process = subprocess.Popen(['ffplay', '-fs', '-an', '-rtmp_buffer', '500', url])
            
            # Wait for the process to complete
            process.wait()
            
            # If the process exits, wait for a few seconds before restarting
            print("Stream disconnected. Showing image and restarting in 5 seconds...")
            show_image(image_path)
            time.sleep(5)
        else:
            print("Stream is not active. Showing image and checking again in 5 seconds...")
            show_image(image_path)
            time.sleep(5)

if __name__ == "__main__":
    stream_url = "rtmp://10.0.0.62/bcs/channel0_ext.bcs?channel=0&stream=0&user=admin&password=curling1"
    image_path = "/home/pi/rpisurv/surveillance/images/connecting.png"  # Replace with the path to your image
    show_image(image_path)
    time.sleep(5)
    start_stream(stream_url, image_path)
