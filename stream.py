import subprocess
import time
import os

def is_stream_active(url):
    try:
        result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type', '-of', 'default=noprint_wrappers=1:nokey=1', url], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        return result.stdout != b''
    except subprocess.TimeoutExpired:
        return False

def is_display_connected(display):
    try:
        result = subprocess.run(['tvservice', '-s', display], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return 'HDMI' in result.stdout.decode()
    except Exception as e:
        print(f"Error checking display {display}: {e}")
        return False

def show_image(image_path, hdmi):
    subprocess.Popen(['feh', '-F', '--on-top', '--auto-zoom', '--fullscreen', '--display', hdmi, image_path])

def start_stream(url, image_path):
    while True:
        if is_stream_active(url):
            print("Stream is active. Starting MPV...")
            subprocess.run(['pkill', 'feh'])
            
            # Start the MPV process for HDMI1
            process_hdmi1 = subprocess.Popen(['mpv', '--fs', '--no-audio', '--drm-connector=HDMI-A-1', url])
            
            # Check if HDMI2 is connected before starting the MPV process for HDMI2
            if is_display_connected('2'):
                process_hdmi2 = subprocess.Popen(['mpv', '--fs', '--no-audio', '--drm-connector=HDMI-A-2', url])
                process_hdmi2.wait()
            
            process_hdmi1.wait()
            
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
