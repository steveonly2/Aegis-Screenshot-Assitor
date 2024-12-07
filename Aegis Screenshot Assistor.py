import win32gui
import win32ui
import win32con
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import json
import threading
import keyboard
import time
from PIL import Image
from discord_webhook import DiscordWebhook, DiscordEmbed
import io

# Window title for Roblox
WINDOW_TITLE = "Roblox"

# Load settings from JSON
def load_settings():
    try:
        with open("settings.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "custom_text": "Hiyah! This is an automated script/F2 test to send screenshots!",
            "gif_path": "",
            "user_id": "",
            "webhook_url": "https://discord.com/api/webhooks/example"
        }

# Save settings to JSON
def save_settings(settings):
    with open("settings.json", "w") as f:
        json.dump(settings, f, indent=4)

# Global variables for settings
settings = load_settings()
custom_text = settings.get("custom_text", "Default Custom Text")
gif_path = settings.get("gif_path", "")
user_id = settings.get("user_id", "")
WEBHOOK_URL = settings.get("webhook_url", "")
capturing = False
selected_hwnd = None

# Capture the entire Roblox window dynamically
def capture_window(hwnd):
    try:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top

        wDC = win32gui.GetWindowDC(hwnd)
        dcObj = win32ui.CreateDCFromHandle(wDC)
        cDC = dcObj.CreateCompatibleDC()
        dataBitMap = win32ui.CreateBitmap()
        dataBitMap.CreateCompatibleBitmap(dcObj, width, height)
        cDC.SelectObject(dataBitMap)
        cDC.BitBlt((0, 0), (width, height), dcObj, (0, 0), win32con.SRCCOPY)

        # Convert to PIL image
        bmpinfo = dataBitMap.GetInfo()
        bmpstr = dataBitMap.GetBitmapBits(True)
        img = Image.frombuffer(
            "RGB", (bmpinfo["bmWidth"], bmpinfo["bmHeight"]),
            bmpstr, "raw", "BGRX", 0, 1
        )
        return img
    except Exception as e:
        print(f"Error capturing window: {e}")
        return None
    finally:
        # Cleanup resources
        cDC.DeleteDC()
        dcObj.DeleteDC()
        win32gui.ReleaseDC(hwnd, wDC)
        win32gui.DeleteObject(dataBitMap.GetHandle())

# Send the screenshot to the webhook
def send_screenshot_to_webhook(screenshot):
    if not WEBHOOK_URL:
        print("Webhook URL is not set. Please configure it in the GUI.")
        return

    try:
        webhook = DiscordWebhook(url=WEBHOOK_URL)
        embed = DiscordEmbed(title="Screenshot Captured", description=custom_text, color=16711680)

        # Attach the screenshot
        with io.BytesIO() as image_binary:
            screenshot.save(image_binary, "PNG")
            image_binary.seek(0)
            webhook.add_file(file=image_binary.read(), filename="screenshot.png")
        embed.set_image(url="attachment://screenshot.png")

        # Attach the GIF if provided
        if gif_path:
            with open(gif_path, "rb") as gif_file:
                webhook.add_file(file=gif_file.read(), filename="custom.gif")
            embed.set_thumbnail(url="attachment://custom.gif")

        webhook.add_embed(embed)
        response = webhook.execute()
        if response.status_code == 200:
            print("Screenshot sent successfully to the webhook.")
        else:
            print(f"Failed to send screenshot: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Error sending screenshot to webhook: {e}")

# List all Roblox windows and allow the user to select one
def select_roblox_window():
    def enum_windows(hwnd, results):
        if win32gui.IsWindowVisible(hwnd) and WINDOW_TITLE in win32gui.GetWindowText(hwnd):
            results.append((hwnd, win32gui.GetWindowText(hwnd)))

    windows = []
    win32gui.EnumWindows(enum_windows, windows)

    if len(windows) > 1:
        window_list = "\n".join(f"{i+1}. {title}" for i, (_, title) in enumerate(windows))
        selection = simpledialog.askinteger(
            "Select Roblox Window",
            f"Multiple Roblox windows detected:\n{window_list}\n\nEnter the number of the window to use:"
        )
        if selection and 1 <= selection <= len(windows):
            return windows[selection - 1][0]
    elif len(windows) == 1:
        return windows[0][0]
    else:
        messagebox.showerror("Error", "No Roblox windows found.")
        return None

# Start capturing screenshots
def capture_screenshot():
    global capturing, selected_hwnd
    print("Automatic capturing started. Press F2 for a manual screenshot.")
    last_capture_time = time.time()
    while capturing:
        try:
            current_time = time.time()
            
            # Send periodic screenshot every 60 seconds
            if current_time - last_capture_time >= 60:
                screenshot = capture_window(selected_hwnd)
                if screenshot:
                    send_screenshot_to_webhook(screenshot)
                    print("Periodic screenshot captured.")
                last_capture_time = current_time

            # Check for manual screenshot with F2
            if keyboard.is_pressed("F2"):
                screenshot = capture_window(selected_hwnd)
                if screenshot:
                    send_screenshot_to_webhook(screenshot)
                    print("Manual screenshot captured.")
                time.sleep(1)  # Prevent multiple triggers
        except Exception as e:
            print(f"Error during capture loop: {e}")
            capturing = False
            break

# Start capturing thread
def on_start_capture():
    global capturing, selected_hwnd
    if not capturing:
        selected_hwnd = select_roblox_window()
        if not selected_hwnd:
            return
        capturing = True
        capture_thread = threading.Thread(target=capture_screenshot)
        capture_thread.daemon = True
        capture_thread.start()
        print("Started capturing screenshots.")
    else:
        messagebox.showinfo("Info", "Already capturing screenshots.")

# Update settings from GUI
def update_settings():
    global custom_text, user_id, WEBHOOK_URL
    custom_text = custom_text_entry.get() or "Default Custom Text"
    user_id = user_id_entry.get()
    WEBHOOK_URL = webhook_url_entry.get() or settings["webhook_url"]

    settings["custom_text"] = custom_text
    settings["user_id"] = user_id
    settings["webhook_url"] = WEBHOOK_URL
    save_settings(settings)

# Select a GIF file
def select_gif():
    global gif_path
    gif_path = filedialog.askopenfilename(title="Select a GIF", filetypes=[("GIF files", "*.gif")])
    if gif_path:
        settings["gif_path"] = gif_path
        save_settings(settings)
    else:
        messagebox.showwarning("Warning", "No file selected.")

def show_credits():
    credits_text = """
    Made by: steveonly2
    Date: 7/12/24

    Developers: Pyt
    """
    messagebox.showinfo("Credits", credits_text)
# GUI for user inputs
def start_gui():
    global custom_text_entry, user_id_entry, webhook_url_entry

    

    root = tk.Tk()
    root.title("Aegis Screenshot Assistor")

    # Custom text input
    tk.Label(root, text="Custom Text:").grid(row=0, column=0, padx=10, pady=10)
    custom_text_entry = tk.Entry(root, width=50)
    custom_text_entry.grid(row=0, column=1, padx=10, pady=10)
    custom_text_entry.insert(0, custom_text)

    # User ID input
    tk.Label(root, text="User ID (for ping):").grid(row=1, column=0, padx=10, pady=10)
    user_id_entry = tk.Entry(root, width=50)
    user_id_entry.grid(row=1, column=1, padx=10, pady=10)
    user_id_entry.insert(0, user_id)

    # Webhook URL input
    tk.Label(root, text="Webhook URL:").grid(row=2, column=0, padx=10, pady=10)
    webhook_url_entry = tk.Entry(root, width=50)
    webhook_url_entry.grid(row=2, column=1, padx=10, pady=10)
    webhook_url_entry.insert(0, WEBHOOK_URL)

    # Button to update settings
    update_button = tk.Button(root, text="Update Settings", command=update_settings)
    update_button.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

    # Button to select GIF
    gif_button = tk.Button(root, text="Select GIF", command=select_gif)
    gif_button.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

    # Button to start capturing
    start_button = tk.Button(root, text="Start Capturing", command=on_start_capture)
    start_button.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

    credits_button = tk.Button(root, text="Credits", command=show_credits)
    credits_button.grid(row=6, column=0, columnspan=2, padx=10, pady=10)

    root.protocol("WM_DELETE_WINDOW", lambda: root.quit())
    root.mainloop()

if __name__ == "__main__":
    start_gui()
