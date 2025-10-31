import os
import shutil
import time
import tkinter as tk
from tkinter import ttk, scrolledtext
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FileSorterHandler(FileSystemEventHandler):
    def __init__(self, watch_folder, sorting_rules, exclude_list, gui_callback=None):
        self.watch_folder = watch_folder
        self.sorting_rules = sorting_rules
        self.exclude_list = exclude_list
        self.gui_callback = gui_callback
        super().__init__()
    
    def log_message(self, message):
        """Send log messages to GUI if available"""
        print(message)
        if self.gui_callback:
            self.gui_callback(message)
    
    def is_excluded(self, filename):
        """Check if file should be excluded based on extension or name"""
        file_extension = os.path.splitext(filename)[1].lower()
        filename_lower = filename.lower()
        
        if file_extension in self.exclude_list:
            return True
        
        for excluded_pattern in self.exclude_list:
            if excluded_pattern in filename_lower and '.' not in excluded_pattern:
                return True
        
        return False
    
    def handle_duplicate(self, destination_path):
        """Handle duplicate files by renaming with incrementing number"""
        base_name = os.path.basename(destination_path)
        directory = os.path.dirname(destination_path)
        name, extension = os.path.splitext(base_name)
        
        counter = 1
        while os.path.exists(destination_path):
            new_name = f"{name} ({counter}){extension}"
            destination_path = os.path.join(directory, new_name)
            counter += 1
        
        return destination_path
    
    def on_created(self, event):
        """Called when a file or directory is created"""
        if event.is_directory:
            return
        
        file_path = event.src_path
        time.sleep(1)  
        self.sort_file(file_path)
    
    def on_moved(self, event):
        """Called when a file or directory is moved"""
        if event.is_directory:
            return
        
        file_path = event.dest_path
        time.sleep(1)
        self.sort_file(file_path)
    
    def sort_file(self, file_path):
        """Sort the file based on its extension"""
        filename = os.path.basename(file_path)
        
        if not os.path.exists(file_path):
            return
        
        if self.is_excluded(filename):
            self.log_message(f"Excluded: {filename} (matches exclude list)")
            return
        
        file_extension = os.path.splitext(filename)[1].lower()
        
        destination_folder = None
        for extension, folder in self.sorting_rules.items():
            if file_extension in extension:
                destination_folder = folder
                break
        
        if not destination_folder or destination_folder == self.watch_folder:
            self.log_message(f"No sorting rule for {filename}, keeping in Downloads")
            return
        
        if not os.path.exists(destination_folder):
            self.log_message(f"Destination folder {destination_folder} doesn't exist, keeping {filename} in Downloads")
            return
        
        os.makedirs(destination_folder, exist_ok=True)
        
        destination_path = os.path.join(destination_folder, filename)
        
        if os.path.exists(destination_path):
            destination_path = self.handle_duplicate(destination_path)
            new_filename = os.path.basename(destination_path)
            self.log_message(f"Duplicate detected: Renaming to {new_filename}")
        
        try:
            shutil.move(file_path, destination_path)
            final_filename = os.path.basename(destination_path)
            self.log_message(f"✓ MOVED: {filename} → {os.path.basename(destination_folder)}/{final_filename}")
        except Exception as e:
            self.log_message(f"✗ Error moving {filename}: {e}")

class FileSorterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart File Sorter")
        self.root.geometry("600x500")
        
        self.observer = None
        self.event_handler = None
        self.is_monitoring = False
        
        self.watch_folder = os.path.expanduser("~/Downloads")
        self.exclude_list = ['.tmp', '.temp', '.crdownload', '.part', '.download']
        
        self.sorting_rules = {
            ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.ico', '.heic'): 
                os.path.expanduser("~/Pictures"),
            ('.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v', '.mpg', '.mpeg'): 
                os.path.expanduser("~/Videos"),
            ('.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.mid', '.midi'): 
                os.path.expanduser("~/Music"),
            ('.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx'): 
                os.path.expanduser("~/Documents"),
        }
        
        self.setup_gui()
        self.check_folders()
    
    def setup_gui(self):
        """Setup the GUI components"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        title_label = ttk.Label(main_frame, text="Smart File Sorter", font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="5")
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="Not Monitoring", foreground="red")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        self.start_button = ttk.Button(button_frame, text="Start Monitoring", command=self.start_monitoring)
        self.start_button.grid(row=0, column=0, padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="Stop Monitoring", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=(0, 5))
        
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="5")
        config_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(config_frame, text="Watch Folder:").grid(row=0, column=0, sticky=tk.W)
        self.watch_folder_var = tk.StringVar(value=self.watch_folder)
        watch_folder_entry = ttk.Entry(config_frame, textvariable=self.watch_folder_var, width=50)
        watch_folder_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        ttk.Label(config_frame, text="Exclude Extensions:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.exclude_var = tk.StringVar(value=", ".join(self.exclude_list))
        exclude_entry = ttk.Entry(config_frame, textvariable=self.exclude_var, width=50)
        exclude_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=(5, 0))
        ttk.Label(config_frame, text="Separate with commas (e.g., .tmp, .crdownload, temp)").grid(row=2, column=1, sticky=tk.W, padx=(5, 0))
        
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding="5")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=70)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
    
    def log_message(self, message):
        """Add message to log with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def check_folders(self):
        """Check if system folders exist"""
        self.log_message("Checking system folders...")
        for extensions, folder in self.sorting_rules.items():
            if os.path.exists(folder):
                self.log_message(f"✓ {os.path.basename(folder)} folder exists")
            else:
                self.log_message(f"✗ {os.path.basename(folder)} folder not found - will skip files for this location")
    
    def update_exclude_list(self):
        """Update exclude list from GUI input"""
        exclude_text = self.exclude_var.get()
        self.exclude_list = [item.strip() for item in exclude_text.split(",") if item.strip()]
    
    def start_monitoring(self):
        """Start the file monitoring"""
        if self.is_monitoring:
            return
        
        self.update_exclude_list()
        self.watch_folder = self.watch_folder_var.get()
        
        if not os.path.exists(self.watch_folder):
            self.log_message(f"Error: Watch folder '{self.watch_folder}' does not exist!")
            return
        
        self.event_handler = FileSorterHandler(
            self.watch_folder, 
            self.sorting_rules, 
            self.exclude_list,
            gui_callback=self.log_message
        )
        
        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.watch_folder, recursive=False)
        
        try:
            self.observer.start()
            self.is_monitoring = True
            self.status_label.config(text="Monitoring Active", foreground="green")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.log_message(f"Started monitoring: {self.watch_folder}")
            self.log_message(f"Exclude list: {', '.join(self.exclude_list)}")
        except Exception as e:
            self.log_message(f"Error starting monitor: {e}")
    
    def stop_monitoring(self):
        """Stop the file monitoring"""
        if not self.is_monitoring or not self.observer:
            return
        
        try:
            self.observer.stop()
            self.observer.join()
            self.is_monitoring = False
            self.status_label.config(text="Not Monitoring", foreground="red")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.log_message("Stopped monitoring")
        except Exception as e:
            self.log_message(f"Error stopping monitor: {e}")
    
    def on_closing(self):
        """Handle application closing"""
        if self.is_monitoring:
            self.stop_monitoring()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = FileSorterGUI(root)
    
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    root.mainloop()

if __name__ == "__main__":
    main()