# File Sorter Pro 

**A smart, automated file organization tool** that monitors your designated folder and automatically sorts files into appropriate system directories based on their file extensions.  
Features a modern GUI with real-time statistics and duplicate handling.

---

## ✨ Features

- **Automated File Sorting:** Monitors a folder and automatically moves files to appropriate directories  
- **Duplicate Handling:** Automatically renames duplicate files with incrementing numbers  
- **Modern GUI:** Beautiful dark/light theme interface with real-time statistics  
- **Customizable Rules:** Configurable file extension rules and exclude patterns  
- **Real-time Logging:** Color-coded activity log with timestamps  
- **Statistics Tracking:** Live counters for files moved, duplicates handled, and errors  

---

## 📁 Supported File Types

### Pictures
`.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff`, `.webp`, `.svg`, `.ico`, `.heic`, `.jiff`, `.jfif`

### Videos
`.mp4`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm`, `.mkv`, `.m4v`, `.mpg`, `.mpeg`

### Music
`.mp3`, `.wav`, `.flac`, `.aac`, `.ogg`, `.m4a`, `.wma`, `.mid`, `.midi`

### Documents
`.pdf`, `.doc`, `.docx`, `.txt`, `.rtf`, `.odt`, `.xls`, `.xlsx`, `.ppt`, `.pptx`

---

## 🛠️ Installation

### Prerequisites
- Python **3.7 or higher**
- **pip** (Python package manager)

### Step 1: Install Required Packages
Open your terminal or command prompt and run:

```bash
pip install customtkinter watchdog
```

### Step 2: Download the Script
Save the Python script as **`file_sorter.py`** in your desired directory.

---

## 🚀 Usage

### Running the Application
1. Open terminal/command prompt in the directory where you saved `file_sorter.py`  
2. Run the script:

```bash
python file_sorter.py
```

### Using the Application
**Configure Settings (optional):**
- Change the watch folder if different from Downloads  
- Modify exclude patterns if needed (default: `.tmp`, `.temp`, `.crdownload`, `.part`, `.download`)

**Start Monitoring:**
- Click the **🚀 Start Monitoring** button  
- The status will change to **"MONITORING" (green)**

**Monitor Activity:**
- Watch the real-time activity log for file movements  
- View statistics for files moved, duplicates handled, and errors  

**Stop Monitoring:**
- Click the **🛑 Stop Monitoring** button when done  
- Or simply close the application (it will ask for confirmation if monitoring is active)

---

## ⚙️ Configuration

### Default Settings
- **Watch Folder:** `~/Downloads` (Your Downloads folder)  
- **Destination Folders:** Standard Windows system folders (Pictures, Videos, Music, Documents)  
- **Excluded Files:** Temporary and incomplete download files  

### Customizing File Rules
You can modify the sorting rules in the script by editing the `sorting_rules` dictionary in the `__init__` method of the `ModernFileSorterApp` class.

### Exclude Patterns
You can exclude specific file types or patterns by:
- **File extensions:** `.tmp`, `.crdownload`  
- **Filename patterns:** `temp`, `tmp` (matches any filename containing these words)

---

## 🐛 Troubleshooting

### Common Issues

**"Module not found" error:**  
- Ensure you installed all requirements:  
  ```bash
  pip install customtkinter watchdog
  ```

**Folder doesn't exist:**  
- The application skips moving files to non-existent destination folders  
- Ensure your system folders (Pictures, Videos, etc.) exist  

**Permission errors:**  
- Run the script as administrator if needed  
- Ensure you have write access to both source and destination folders  

**Files not moving:**  
- Check the exclude patterns  
- Verify the file extension is supported  
- Check the activity log for error messages  

---

## 📝 Notes

- The application only moves files to **existing system folders**  
- Duplicate files are automatically renamed (e.g., `file (1).jpg`, `file (2).jpg`)  
- The application waits briefly after detecting new files to ensure downloads are complete  
- Statistics are reset each time the application starts  

---

## 🔒 Privacy

- The application runs **locally** on your machine  
- **No data** is sent to external servers  
- File operations are logged **only locally** in the application interface  

---
