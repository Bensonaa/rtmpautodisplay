import subprocess
import time

def is_stream_active(url):
    try:
        # Run ffprobe to check the stream status
        result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type', '-of', 'default=noprint_wrappers=1:nokey=1', url], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        # If ffprobe returns any output, the stream is active
        return result.stdout != b''
    except subprocess.TimeoutExpired:
        return False

def start_stream(url):
    while True:
        if is_stream_active(url):
            print("Stream is active. Starting ffplay...")
            # Start the ffplay process with fullscreen, no audio, and minimal latency
            process = subprocess.Popen(['ffplay', '-fs', '-an', '-rtmp_buffer', '500', url])
            
            # Wait for the process to complete
            process.wait()
            
            # If the process exits, wait for a few seconds before restarting
            print("Stream disconnected. Restarting in 5 seconds...")
            time.sleep(5)
        else:
            print("Stream is not active. Checking again in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    stream_url = "rtmp://10.0.0.62/bcs/channel0_ext.bcs?channel=0&stream=0&user=admin&password=curling1"
    start_stream(stream_url)
