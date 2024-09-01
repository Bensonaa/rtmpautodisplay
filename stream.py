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
            # Start the ffplay process with fullscreen, no audio, and minimal latency
            process = subprocess.Popen(['ffplay', '-fs', '-an', '-fflags', 'nobuffer', '-flags', 'low_delay', '-i', url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for the process to complete
            process.wait()
            
            # If the process exits, wait for a few seconds before restarting
            print("Stream disconnected. Restarting in 5 seconds...")
            time.sleep(5)
        else:
            print("Stream is not active. Checking again in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    stream_url = "rtmp://your_stream_url_here"
    start_stream(stream_url)
