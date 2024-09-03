import subprocess
import time
import logging

# Configure logging to output to a file
try:
    logging.basicConfig(filename='stream_monitor.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Logging is configured correctly.")
except Exception as e:
    print(f"Error configuring logging: {e}")

def is_connectable(url):
    try:
        ffprobeoutput = subprocess.run(
            ['ffprobe', '-v', 'error', '-i', url, '-show_entries', 'stream=codec_type', '-of', 'default=noprint_wrappers=1:nokey=1'],
            timeout=20, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return ffprobeoutput.returncode == 0
    except subprocess.TimeoutExpired:
        logging.error("ffprobe timed out. Try increasing the probe timeout.")
        return False
    except Exception as e:
        logging.error(f"Error checking stream: {e}")
        return False

def show_image(image_path):
    subprocess.Popen(['feh', '-F', image_path])

def start_stream(url, image_path):
    process = None
    while True:
        if is_connectable(url):
            if process is None or process.poll() is not None:
                logging.info("Stream is active. Starting ffplay...")
                subprocess.run(['pkill', 'feh'])
                process = subprocess.Popen(
                    ['ffplay', '-fs', '-an', '-buffer_size', '65536', url],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
        else:
            if process is not None and process.poll() is None:
                logging.info("Stream is not active. Killing ffplay process...")
                process.terminate()
                process.wait()
                process = None
                time.sleep(5)  # Add a delay before restarting
            logging.info("Showing image and checking again in 10 seconds...")
            show_image(image_path)
        
        time.sleep(10)

if __name__ == "__main__":
    stream_url = "rtmp://10.0.0.62/bcs/channel0_ext.bcs?channel=0&stream=0&user=admin&password=curling1"
    image_path = "/home/pi/rpisurv/surveillance/images/connecting.png"
    show_image(image_path)
    time.sleep(5)
    start_stream(stream_url, image_path)
