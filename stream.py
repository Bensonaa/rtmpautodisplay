import subprocess
import time
import threading
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

def is_connectable(url):
    try:
        ffprobeoutput = subprocess.run(
            ['ffprobe', '-v', 'error', '-i', url, '-show_entries', 'stream=codec_type', '-of', 'default=noprint_wrappers=1:nokey=1'],
            timeout=10, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return ffprobeoutput.returncode == 0
    except subprocess.TimeoutExpired:
        log_message("ffprobe timed out. Try increasing the probe timeout.")
        return False
    except Exception as e:
        log_message(f"Error checking stream: {e}")
        return False

def show_image(image_path):
    subprocess.Popen(['feh', '-F', image_path])

def start_stream(url, image_path):
    process = None
    while True:
        if is_connectable(url):
            if process is None or process.poll() is not None:
                log_message("Stream is active. Starting ffplay...")
                subprocess.run(['pkill', 'feh'])
                process = subprocess.Popen(
                    ['ffplay', '-fs', '-an', '-fflags', 'nobuffer', '-flags', 'low_delay', '-strict', 'experimental', '-rtmp_buffer', '100', url],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                threading.Thread(target=freeze_monitor, args=(process,)).start()
        else:
            if process is not None and process.poll() is None:
                log_message("Stream is not active. Killing ffplay process...")
                process.terminate()
                process.wait()
                process = None
            log_message("Showing image and checking again in 10 seconds...")
            show_image(image_path)
        
        time.sleep(10)

def freeze_monitor(process):
    while True:
        output = process.stderr.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            if "freeze_start" in output:
                process.kill()
                log_message("Stream froze. Killing ffplay process and showing image...")
                show_image(image_path)
                return
            log_message(output.strip())

def log_message(message):
    log_window.insert(tk.END, message + '\n')
    log_window.see(tk.END)

def create_log_window():
    root = tk.Tk()
    root.title("Log Messages")
    global log_window
    log_window = ScrolledText(root, wrap=tk.WORD, width=100, height=30)
    log_window.pack(padx=10, pady=10)
    threading.Thread(target=root.mainloop).start()

if __name__ == "__main__":
    stream_url = "rtmp://10.0.0.62/bcs/channel0_ext.bcs?channel=0&stream=0&user=admin&password=curling1"
    image_path = "/home/pi/rpisurv/surveillance/images/connecting.png"
    create_log_window()
    show_image(image_path)
    time.sleep(5)
    start_stream(stream_url, image_path)
