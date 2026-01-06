import subprocess
import time
import threading
import logging
import psutil

class StreamManager:
    def __init__(self, url1, url2=None, image_path=None):
        self.url1 = url1
        self.url2 = url2
        self.image_path = image_path
        self.lock = threading.Lock()
        self.ffplay_processes = []

    def is_stream_active(self, url):
        """
        Uses ffprobe to quickly check if the stream is accessible before trying to play it.
        """
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type', '-of', 'default=noprint_wrappers=1:nokey=1', url],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )
            return result.stdout != b''
        except subprocess.TimeoutExpired:
            logging.error(f"Timeout expired while checking stream: {url}")
            return False
        except Exception as e:
            logging.error(f"Error checking stream {url}: {e}")
            return False

    def play_stream(self, url, x, y, width, height):
        """
        Launches ffplay with Raspberry Pi hardware acceleration.
        """
        command = [
            'ffplay', 
            '-vcodec', 'h264_v4l2m2m', 
            '-rtsp_transport', 'tcp',  # <--- ADD THIS LINE
            '-x', str(width), 
            '-y', str(height), 
            '-left', str(x), 
            '-top', str(y), 
            '-noborder', 
            '-loglevel', 'quiet', 
            '-sync', 'ext',  
            url
        ]
        
        ffplay_process = None
        
        with self.lock:
            ffplay_process = subprocess.Popen(command)
            self.ffplay_processes.append(ffplay_process)
            
        try:
            # communicate() blocks this thread until the process exits
            ffplay_process.communicate()
        except Exception as e:
            logging.error(f"Error playing stream {url}: {e}")
        finally:
            # Cleanup when the process dies
            if ffplay_process:
                ffplay_process.terminate()
                try:
                    ffplay_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    ffplay_process.kill()
                
                with self.lock:
                    if ffplay_process in self.ffplay_processes:
                        self.ffplay_processes.remove(ffplay_process)

    def monitor_cpu_usage(self):
        """
        Watchdog: Checks if ffplay is using CPU. If <5%, it assumes the stream is frozen/black
        and kills the process to force a restart.
        """
        while True:
            # 1. Copy the list safely so we don't hold the lock while measuring CPU
            with self.lock:
                current_procs = list(self.ffplay_processes)

            # 2. Iterate over the copy
            for process in current_procs:
                try:
                    p = psutil.Process(process.pid)
                    # This call blocks for 1 second to measure usage
                    cpu_usage = p.cpu_percent(interval=1)
                    
                    if cpu_usage < 5:  # Threshold for "Frozen"
                        logging.warning(f"Low CPU ({cpu_usage}%) detected for PID {process.pid}. Restarting stream...")
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                        
                        # We don't need to remove it from the list here; 
                        # the play_stream function's 'finally' block handles cleanup.
                
                except psutil.NoSuchProcess:
                    pass  # Process already dead, ignore
                except Exception as e:
                    logging.error(f"Error in monitor: {e}")

            time.sleep(20) # Check every 20 seconds

    def start_stream(self):
        """
        Main loop: Checks if threads are alive. If not, restarts them.
        """
        # Start the watchdog as a daemon (background) thread
        monitor_thread = threading.Thread(target=self.monitor_cpu_usage, daemon=True)
        monitor_thread.start()

        thread1 = None
        thread2 = None

        logging.info("Stream Manager Started.")

        while True:
            # --- Stream 1 Management ---
            if thread1 is None or not thread1.is_alive():
                if self.is_stream_active(self.url1):
                    logging.info(f"Starting Stream 1 on Left...")
                    thread1 = threading.Thread(target=self.play_stream, args=(self.url1, 0, 0, 1920, 1080))
                    thread1.start()
                else:
                    logging.warning("Stream 1 unavailable. Retrying in 5s...")

            # --- Stream 2 Management ---
            if self.url2:
                if thread2 is None or not thread2.is_alive():
                    if self.is_stream_active(self.url2):
                        logging.info(f"Starting Stream 2 on Right...")
                        thread2 = threading.Thread(target=self.play_stream, args=(self.url2, 1920, 0, 1920, 1080))
                        thread2.start()
                    else:
                        logging.warning("Stream 2 unavailable. Retrying in 5s...")

            # Wait before checking status again to prevent CPU spinning
            time.sleep(5)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("stream_manager.log"),
            logging.StreamHandler()
        ]
    )
    
    # EDIT YOUR CONFIG HERE
    stream_url1 = "rtmp://192.168.1.74/bcs/channel0_ext.bcs?channel=0&stream=0&user=admin&password=curling1"
    stream_url2 = None # Set this to a URL string if you have a second stream
    image_path = "/home/pi/rtmpautodisplay/placeholder.png"
    
    stream_manager = StreamManager(stream_url1, stream_url2, image_path)
    try:
        stream_manager.start_stream()
    except KeyboardInterrupt:
        logging.info("Stopping Stream Manager...")
