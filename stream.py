import subprocess
import time
import os

def is_stream_active(url):
    try:
        result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type', '-of', 'default=noprint_wrappers=1:nokey=1', url], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        return result.stdout != b''
    except subprocess.TimeoutExpired:
        return False

def get_connected_displays():
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

def show_image(image_path, display):
    subprocess.Popen(['feh', '-F', '--on-top', '--auto-zoom', '--fullscreen', '--display', display, image_path])

def start_stream(url, image_path):
    while True:
        if is_stream_active(url):
            print("Stream is active. Starting ffplay...")
            subprocess.run(['pkill', 'feh'])
            
            connected_displays = get_connected_displays()
            if connected_displays:
                processes = []
                for display in connected_displays:
                    process = subprocess.Popen(['ffplay', '-fs', '-an', '-vcodec', 'h264_v4l2m2m', '-i', url])
                    processes.append(process)
                
                for process in processes:
                    process.wait()
            else:
                print("No active displays connected.")
            
            print("Stream disconnected. Showing image and restarting in 5 seconds...")
            for display in connected_displays:
                show_image(image_path, display)
            time.sleep(5)
        else:
            print("Stream is not active. Showing image and checking again in 5 seconds...")
            connected_displays = get_connected_displays()
            for display in connected_displays:
                show_image(image_path, display)
            time.sleep(5)

if __name__ == "__main__":
    stream_url = "rtmp://10.0.0.62/bcs/channel0_ext.bcs?channel=0&stream=0&user=admin&password=curling1"
    image_path = "/home/pi/rpisurv/surveillance/images/connecting.png"
    connected_displays = get_connected_displays()
    for display in connected_displays:
        show_image(image_path, display)
    time.sleep(5)
    start_stream(stream_url, image_path)
