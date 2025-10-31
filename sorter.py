import os
import shutil
import time
import customtkinter as ctk
from tkinter import messagebox, filedialog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Set appearance mode and color theme
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class ModernFileSorterHandler(FileSystemEventHandler):
    def __init__(self, watch_folder, sorting_rules, exclude_list, gui_callback=None):
        self.watch_folder = watch_folder
        self.sorting_rules = sorting_rules
        self.exclude_list = exclude_list
        self.gui_callback = gui_callback
        super().__init__()
    
    def log_message(self, message, message_type="info"):
        if self.gui_callback:
            self.gui_callback(message, message_type)
    
    def is_excluded(self, filename):
        file_extension = os.path.splitext(filename)[1].lower()
        filename_lower = filename.lower()
        
        if file_extension in self.exclude_list:
            return True
        
        for excluded_pattern in self.exclude_list:
            if excluded_pattern in filename_lower and '.' not in excluded_pattern:
                return True
        return False
    
    def handle_duplicate(self, destination_path):
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
        if event.is_directory:
            return
        file_path = event.src_path
        time.sleep(0.5)
        self.sort_file(file_path)
    
    def on_moved(self, event):
        if event.is_directory:
            return
        file_path = event.dest_path
        time.sleep(0.5)
        self.sort_file(file_path)
    
    def sort_file(self, file_path):
        filename = os.path.basename(file_path)
        
        if not os.path.exists(file_path):
            return
        
        if self.is_excluded(filename):
            self.log_message(f"Excluded: {filename} (matches exclude list)", "warning")
            return
        
        file_extension = os.path.splitext(filename)[1].lower()
        
        destination_folder = None
        for extension, folder in self.sorting_rules.items():
            if file_extension in extension:
                destination_folder = folder
                break
        
        if not destination_folder or destination_folder == self.watch_folder:
            self.log_message(f"No sorting rule for {filename}, keeping in Downloads", "info")
            return
        
        if not os.path.exists(destination_folder):
            self.log_message(f"Destination folder doesn't exist, keeping {filename}", "error")
            return
        
        os.makedirs(destination_folder, exist_ok=True)
        destination_path = os.path.join(destination_folder, filename)
        
        if os.path.exists(destination_path):
            destination_path = self.handle_duplicate(destination_path)
            new_filename = os.path.basename(destination_path)
            self.log_message(f"Duplicate detected: Renaming to {new_filename}", "warning")
        
        try:
            shutil.move(file_path, destination_path)
            final_filename = os.path.basename(destination_path)
            self.log_message(f"✓ MOVED: {filename} → {os.path.basename(destination_folder)}", "success")
        except Exception as e:
            self.log_message(f"✗ Error moving {filename}: {e}", "error")

class ModernFileSorterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("File Sorter Pro 🚀")
        self.geometry("900x700")
        self.minsize(800, 600)
        
        # Configuration
        self.watch_folder = os.path.expanduser("~/Downloads")
        self.exclude_list = ['.tmp', '.temp', '.crdownload', '.part', '.download']
        self.is_monitoring = False
        self.observer = None
        self.event_handler = None
        
        self.sorting_rules = {
            ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.ico', '.heic', '.jiff', '.jfif'): 
                os.path.expanduser("~/Pictures"),
            ('.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v', '.mpg', '.mpeg'): 
                os.path.expanduser("~/Videos"),
            ('.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.mid', '.midi'): 
                os.path.expanduser("~/Music"),
            ('.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx'): 
                os.path.expanduser("~/Documents"),
        }
        
        # Initialize statistics
        self.files_moved = 0
        self.duplicates_handled = 0
        self.errors_count = 0
        
        self.setup_ui()
        self.check_folders()
    
    def setup_ui(self):
        # Create main grid
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Header
        header_frame = ctk.CTkFrame(self, corner_radius=0)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_columnconfigure(1, weight=1)
        
        # App icon and title
        icon_label = ctk.CTkLabel(header_frame, text="📁", font=ctk.CTkFont(size=24))
        icon_label.grid(row=0, column=0, padx=20, pady=15)
        
        title_label = ctk.CTkLabel(header_frame, text="File Sorter Pro", 
                                  font=ctk.CTkFont(size=24, weight="bold"))
        title_label.grid(row=0, column=1, padx=10, pady=15, sticky="w")
        
        # Status indicator
        self.status_label = ctk.CTkLabel(header_frame, text="● STOPPED", 
                                        text_color="#e74c3c", font=ctk.CTkFont(weight="bold"))
        self.status_label.grid(row=0, column=2, padx=20, pady=15)
        
        # Main content area
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(3, weight=1)
        
        # Control Section
        control_frame = ctk.CTkFrame(main_frame)
        control_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=(0, 20))
        control_frame.grid_columnconfigure(1, weight=1)
        
        # Folder selection
        ctk.CTkLabel(control_frame, text="Watch Folder:", 
                    font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=20, pady=15, sticky="w")
        
        self.folder_entry = ctk.CTkEntry(control_frame, placeholder_text="Select folder to monitor...")
        self.folder_entry.grid(row=0, column=1, padx=10, pady=15, sticky="ew")
        self.folder_entry.insert(0, self.watch_folder)
        
        browse_btn = ctk.CTkButton(control_frame, text="Browse", width=100, 
                                  command=self.browse_folder)
        browse_btn.grid(row=0, column=2, padx=20, pady=15)
        
        # Control buttons
        button_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        button_frame.grid(row=1, column=0, columnspan=3, padx=20, pady=(0, 15))
        
        self.start_btn = ctk.CTkButton(button_frame, text="🚀 Start Monitoring", 
                                      command=self.start_monitoring,
                                      fg_color="#27ae60", hover_color="#219a52")
        self.start_btn.pack(side="left", padx=(0, 10))
        
        self.stop_btn = ctk.CTkButton(button_frame, text="🛑 Stop Monitoring", 
                                     command=self.stop_monitoring,
                                     fg_color="#e74c3c", hover_color="#c0392b",
                                     state="disabled")
        self.stop_btn.pack(side="left")
        
        # Configuration Section
        config_frame = ctk.CTkFrame(main_frame)
        config_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=0, pady=(0, 20))
        config_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(config_frame, text="Exclude Patterns:", 
                    font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=20, pady=15, sticky="w")
        
        self.exclude_entry = ctk.CTkEntry(config_frame, 
                                         placeholder_text=".tmp, .crdownload, temp, ...")
        self.exclude_entry.grid(row=0, column=1, padx=10, pady=15, sticky="ew")
        self.exclude_entry.insert(0, ", ".join(self.exclude_list))
        
        # Statistics Section
        stats_frame = ctk.CTkFrame(main_frame)
        stats_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=0, pady=(0, 20))
        stats_frame.grid_columnconfigure(0, weight=1)
        stats_frame.grid_columnconfigure(1, weight=1)
        stats_frame.grid_columnconfigure(2, weight=1)
        
        self.files_moved_label = ctk.CTkLabel(stats_frame, text="Files Moved: 0", 
                                             font=ctk.CTkFont(weight="bold"))
        self.files_moved_label.grid(row=0, column=0, padx=20, pady=15)
        
        self.duplicates_label = ctk.CTkLabel(stats_frame, text="Duplicates Handled: 0", 
                                           font=ctk.CTkFont(weight="bold"))
        self.duplicates_label.grid(row=0, column=1, padx=20, pady=15)
        
        self.errors_label = ctk.CTkLabel(stats_frame, text="Errors: 0", 
                                       font=ctk.CTkFont(weight="bold"))
        self.errors_label.grid(row=0, column=2, padx=20, pady=15)
        
        # Log Section
        log_frame = ctk.CTkFrame(main_frame)
        log_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=0, pady=0)
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)
        
        log_header = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_header.grid(row=0, column=0, sticky="ew", padx=20, pady=15)
        log_header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(log_header, text="Activity Log", 
                    font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, sticky="w")
        
        clear_btn = ctk.CTkButton(log_header, text="Clear Log", width=100, 
                                 command=self.clear_log)
        clear_btn.grid(row=0, column=1, sticky="e")
        
        # Use a standard tkinter Text widget for colored logging
        from tkinter import Text
        self.log_text = Text(log_frame, font=("Consolas", 11), bg="#2b2b2b", fg="#ffffff", 
                           insertbackground="white", wrap="word")
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # Add scrollbar to the Text widget
        scrollbar = ctk.CTkScrollbar(log_frame, command=self.log_text.yview)
        scrollbar.grid(row=1, column=1, sticky="ns", pady=(0, 20))
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # Configure text tags for coloring
        self.log_text.tag_configure("timestamp", foreground="gray")
        self.log_text.tag_configure("info", foreground="#3498db")
        self.log_text.tag_configure("success", foreground="#27ae60")
        self.log_text.tag_configure("warning", foreground="#f39c12")
        self.log_text.tag_configure("error", foreground="#e74c3c")
    
    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.watch_folder)
        if folder:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)
    
    def clear_log(self):
        self.log_text.delete("1.0", "end")
    
    def log_message(self, message, message_type="info"):
        timestamp = time.strftime("%H:%M:%S")
        
        # Insert message with appropriate tag
        self.log_text.insert("end", f"[{timestamp}] ", "timestamp")
        self.log_text.insert("end", message + "\n", message_type)
        self.log_text.see("end")
        
        # Only update statistics for actual file operations, not status messages
        if message_type == "success" and "MOVED:" in message:
            self.files_moved += 1
            self.files_moved_label.configure(text=f"Files Moved: {self.files_moved}")
        elif message_type == "warning" and "duplicate" in message.lower():
            self.duplicates_handled += 1
            self.duplicates_label.configure(text=f"Duplicates Handled: {self.duplicates_handled}")
        elif message_type == "error" and "Error moving" in message:
            self.errors_count += 1
            self.errors_label.configure(text=f"Errors: {self.errors_count}")
    
    def check_folders(self):
        # Use a special message type for initialization that doesn't affect statistics
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] ", "timestamp")
        self.log_text.insert("end", "🔍 Checking system folders...\n", "info")
        
        for extensions, folder in self.sorting_rules.items():
            timestamp = time.strftime("%H:%M:%S")
            self.log_text.insert("end", f"[{timestamp}] ", "timestamp")
            if os.path.exists(folder):
                self.log_text.insert("end", f"✅ {os.path.basename(folder)} folder exists\n", "info")
            else:
                self.log_text.insert("end", f"❌ {os.path.basename(folder)} folder not found\n", "warning")
        
        self.log_text.see("end")
    
    def update_exclude_list(self):
        exclude_text = self.exclude_entry.get()
        self.exclude_list = [item.strip() for item in exclude_text.split(",") if item.strip()]
    
    def start_monitoring(self):
        if self.is_monitoring:
            return
        
        self.update_exclude_list()
        self.watch_folder = self.folder_entry.get()
        
        if not os.path.exists(self.watch_folder):
            self.log_message(f"❌ Watch folder doesn't exist!", "error")
            messagebox.showerror("Error", "Please select a valid watch folder!")
            return
        
        self.event_handler = ModernFileSorterHandler(
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
            
            # Update UI
            self.status_label.configure(text="● MONITORING", text_color="#27ae60")
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            
            self.log_message("🚀 Started monitoring files", "info")
            self.log_message(f"📂 Watching: {self.watch_folder}", "info")
            
        except Exception as e:
            self.log_message(f"❌ Failed to start: {e}", "error")
    
    def stop_monitoring(self):
        if not self.is_monitoring:
            return
        
        try:
            self.observer.stop()
            self.observer.join()
            self.is_monitoring = False
            
            # Update UI
            self.status_label.configure(text="● STOPPED", text_color="#e74c3c")
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            
            self.log_message("🛑 Stopped monitoring", "info")
            
        except Exception as e:
            self.log_message(f"❌ Error stopping: {e}", "error")
    
    def on_closing(self):
        if self.is_monitoring:
            if messagebox.askyesno("Quit", "Monitoring is active. Stop and quit?"):
                self.stop_monitoring()
                self.destroy()
        else:
            self.destroy()

def main():
    app = ModernFileSorterApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()

if __name__ == "__main__":
    main()