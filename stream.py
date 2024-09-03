import subprocess
import time
import os

def is_stream_active(url):
    try:
        result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type', '-of', 'default=noprint_wrappers=1:nokey=1', url], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        return result.stdout != b''
    except subprocess.TimeoutExpired:
        return False

def show_image(image_path, hdmi):
    subprocess.Popen(['feh', '-F', '--on-top', '--auto-zoom', '--fullscreen', '--display', hdmi, image_path])

def start_stream(url, image_path):
    while True:
        if is_stream_active(url):
            print("Stream is active. Starting GStreamer...")
            subprocess.run(['pkill', 'feh'])
            
            # Start the GStreamer process for both HDMI outputs
            process_hdmi1 = subprocess.Popen(['gst-launch-1.0', 'rtspsrc', 'location=' + url, '!', 'decodebin', '!', 'videoconvert', '!', 'autovideosink', 'display=HDMI-1'])
            process_hdmi2 = subprocess.Popen(['gst-launch-1.0', 'rtspsrc', 'location=' + url, '!', 'decodebin', '!', 'videoconvert', '!', 'autovideosink', 'display=HDMI-2'])
            
            # Wait for the processes to complete
            process_hdmi1.wait()
            process_hdmi2.wait()
            
            print("Stream disconnected. Showing image and restarting in 5 seconds...")
            show_image(image_path, 'hdmi')
            show_image(image_path, 'hdmi2')
            time.sleep(5)
        else:
            print("Stream is not active. Showing image and checking again in 5 seconds...")
            show_image(image_path, 'hdmi')
            show_image(image_path, 'hdmi2')
            time.sleep(5)

if __name__ == "__main__":
    stream_url = "rtmp://10.0.0.62/bcs/channel0_ext.bcs?channel=0&stream=0&user=admin&password=curling1"
    image_path = "/home/pi/rpisurv/surveillance/images/connecting.png"
    show_image(image_path, 'hdmi')
    show_image(image_path, 'hdmi2')
    time.sleep(5)
    start_stream(stream_url, image_path)
