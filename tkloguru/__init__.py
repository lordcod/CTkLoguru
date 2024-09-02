import tkinter as tk
from tkinter import ttk
import queue
from loguru import logger
import sys
import threading

class LoguruWidget(ttk.Frame):
    def __init__(self, master=None, show_scrollbar=True, color_mode='level', max_lines=1000, **kwargs):
        super().__init__(master, **kwargs)
        self.queue = queue.Queue()
        self.show_scrollbar = show_scrollbar
        self.color_mode = color_mode  # 'level', 'message', or 'full'
        self.max_lines = max_lines
        self.create_widgets()
        self.after(100, self.check_queue)

    def create_widgets(self):
        self.text = tk.Text(self, wrap=tk.WORD, state=tk.DISABLED)
        
        if self.show_scrollbar:
            self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
            self.text.configure(yscrollcommand=self.scrollbar.set)
            self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.text.pack(expand=True, fill=tk.BOTH)
        
        # Configure tags for different log levels with colors
        self.text.tag_configure("DEBUG", foreground="#4a4a4a")  # Dark gray
        self.text.tag_configure("INFO", foreground="#3498db")   # Blue
        self.text.tag_configure("SUCCESS", foreground="#2ecc71")  # Green
        self.text.tag_configure("WARNING", foreground="#f39c12")  # Orange
        self.text.tag_configure("ERROR", foreground="#e74c3c")    # Red
        self.text.tag_configure("CRITICAL", foreground="white", background="#c0392b")  # White on dark red

    def check_queue(self):
        try:
            while self.queue.qsize():
                record = self.queue.get_nowait()
                self.update_widget(record)
        except queue.Empty:
            pass
        finally:
            self.after(100, self.check_queue)

    def update_widget(self, record):
        self.text.configure(state=tk.NORMAL)
        
        time_str = record["time"].strftime("%Y-%m-%d %H:%M:%S")
        level = record["level"].name
        message = record["message"]
        
        if self.color_mode == 'full':
            self.text.insert(tk.END, f"{time_str} | {level:8} | {message}\n", level)
        elif self.color_mode == 'message':
            self.text.insert(tk.END, f"{time_str} | {level:8} | ", "")
            self.text.insert(tk.END, f"{message}\n", level)
        else:  # 'level' mode (default)
            self.text.insert(tk.END, f"{time_str} | ", "")
            self.text.insert(tk.END, f"{level:8}", level)
            self.text.insert(tk.END, f" | {message}\n", "")
        
        # Limit the number of lines in the widget
        if int(self.text.index('end-1c').split('.')[0]) > self.max_lines:
            self.text.delete('1.0', '2.0')
        
        self.text.see(tk.END)
        self.text.configure(state=tk.DISABLED)

    def sink(self, message):
        record = message.record
        self.queue.put(record)

def setup_logger(widget):
    logger.remove()
    logger.add(widget.sink, backtrace=True, diagnose=True)

# Example usage
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Thread-Safe Loguru Tkinter Widget")
    root.geometry("600x400")

    # Choose color_mode from: 'level', 'message', or 'full'
    log_widget = LoguruWidget(root, show_scrollbar=True, color_mode='level', max_lines=1000)
    log_widget.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

    setup_logger(log_widget)

    # Add console handler for debugging
    logger.add(sys.stdout, level="DEBUG")

    # Example log messages
    def generate_logs():
        logger.debug("This is a debug message")
        logger.info("This is an info message")
        logger.success("This is a success message")
        logger.warning("This is a warning message")
        logger.error("This is an error message")
        logger.critical("This is a critical message")

    # Run log generation in a separate thread
    threading.Thread(target=generate_logs).start()

    root.mainloop()