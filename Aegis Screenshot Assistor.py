import time
import win32gui
import win32ui
import win32con
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog
import json
import threading
import keyboard
from PIL import Image
from discord_webhook import DiscordWebhook, DiscordEmbed
import io
import os
from datetime import datetime


# MADE BY steveonly2,steveonly4,Steve ( my multiple names depending on the platform lol, Steve is my real name)
# project's v6.0 
WINDOW_TITLE = "Roblox"

DEFAULT_SETTINGS = {
    "custom_text": "Hiyah! This is an automated script/F2 test to send screenshots!",
    "gif_path": "",
    "user_id": "",
    "webhook_url": "https://discord.com/api/webhooks/example",
    "screenshot_delay": 60, 
    "dark_mode": False  
}

def check_and_create_settings():
    if not os.path.exists("settings.json"):
        with open("settings.json", "w") as f:
            json.dump(DEFAULT_SETTINGS, f, indent=4)


def load_settings():
    check_and_create_settings() 
    try:
        with open("settings.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return DEFAULT_SETTINGS

def save_settings(settings):
    with open("settings.json", "w") as f:
        json.dump(settings, f, indent=4)


settings = load_settings()
custom_text = settings.get("custom_text", "Default Custom Text")
gif_path = settings.get("gif_path", "")
user_id = settings.get("user_id", "")
WEBHOOK_URL = settings.get("webhook_url", "")
screenshot_delay = settings.get("screenshot_delay", 60)  
capturing = False
selected_hwnd = None
start_time = None  
window_name = ""   
dark_mode = settings.get("dark_mode", False)  


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

        bmpinfo = dataBitMap.GetInfo()
        bmpstr = dataBitMap.GetBitmapBits(True)
        img = Image.frombytes(
            "RGB", (bmpinfo["bmWidth"], bmpinfo["bmHeight"]),
            bmpstr, "raw", "BGRX", 0, 1
        )
        return img
    except Exception as e:
        print(f"Error capturing window: {e}")
        return None
    finally:
        cDC.DeleteDC()
        dcObj.DeleteDC()
        win32gui.ReleaseDC(hwnd, wDC)
        win32gui.DeleteObject(dataBitMap.GetHandle())


def send_screenshot_to_webhook(screenshot):
    if not WEBHOOK_URL:
        print("Webhook URL is not set. Please configure it in the GUI.")
        return

    try:
        
        elapsed_time = time.time() - start_time
        elapsed_time_str = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))

        
        current_date = datetime.now().strftime("%d %B %Y")  

       
        embed = DiscordEmbed(title="Screenshot Captured", description=custom_text, color=16711680)
        embed.add_embed_field(name="Time Elapsed", value=elapsed_time_str, inline=True)
        embed.add_embed_field(name="Date", value=current_date, inline=True)  # Added Date to embed
        embed.add_embed_field(name="Window Name", value=window_name, inline=True)

        with io.BytesIO() as image_binary:
            screenshot.save(image_binary, "PNG")
            image_binary.seek(0)
            webhook = DiscordWebhook(url=WEBHOOK_URL)
            webhook.add_file(file=image_binary.read(), filename="screenshot.png")
        embed.set_image(url="attachment://screenshot.png")

       
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

def show_credits():
    credits_text = """
    Made by: steveonly2
    Date: 7/12/24

    Developers: Steve, Pyt
    """
    messagebox.showinfo("Credits", credits_text)


def capture_screenshot():
    global capturing, selected_hwnd, start_time, window_name
    print("Automatic capturing started. Press F2 for a manual screenshot.")
    last_capture_time = time.time()
    while capturing:
        try:
            current_time = time.time()

            if current_time - last_capture_time >= screenshot_delay:
                screenshot = capture_window(selected_hwnd)
                if screenshot:
                    send_screenshot_to_webhook(screenshot)
                    print("Periodic screenshot captured.")
                last_capture_time = current_time

            if keyboard.is_pressed("F2"):
                screenshot = capture_window(selected_hwnd)
                if screenshot:
                    send_screenshot_to_webhook(screenshot)
                    print("Manual screenshot captured.")
                time.sleep(1) 
        except Exception as e:
            print(f"Error during capture loop: {e}")
            capturing = False
            break


def on_start_capture():
    global capturing, selected_hwnd, start_time, window_name
    if not capturing:
        selected_hwnd = select_roblox_window()
        if not selected_hwnd:
            return

        window_name = win32gui.GetWindowText(selected_hwnd)
        start_time = time.time()
        capturing = True
        capture_thread = threading.Thread(target=capture_screenshot)
        capture_thread.daemon = True
        capture_thread.start()
        print("Started capturing screenshots.")
    else:
        messagebox.showinfo("Info", "Already capturing screenshots.")


def on_stop_capture():
    global capturing
    if capturing:
        capturing = False
        print("Stopped capturing screenshots.")
    else:
        messagebox.showinfo("Info", "No capturing in progress.")

def update_settings():
    global custom_text, user_id, WEBHOOK_URL, screenshot_delay, dark_mode
    custom_text = custom_text_entry.get() or "Default Custom Text"
    user_id = user_id_entry.get()
    WEBHOOK_URL = webhook_url_entry.get() or settings["webhook_url"]
    try:
        screenshot_delay = int(screenshot_delay_entry.get())
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a valid number for delay in seconds.")
        return

    dark_mode = dark_mode_var.get()   
    settings["custom_text"] = custom_text
    settings["user_id"] = user_id
    settings["webhook_url"] = WEBHOOK_URL
    settings["screenshot_delay"] = screenshot_delay
    settings["dark_mode"] = dark_mode
    save_settings(settings)

 
    if dark_mode:
        ctk.set_appearance_mode("dark")
    else:
        ctk.set_appearance_mode("light")

    messagebox.showinfo("Success", "Settings successfully updated.")

def select_gif():
    global gif_path
    gif_path = filedialog.askopenfilename(title="Select a GIF", filetypes=[("GIF files", "*.gif")])
    if gif_path:
        settings["gif_path"] = gif_path
        save_settings(settings)
    else:
        messagebox.showwarning("Warning", "No file selected.")

# GUI for user inputs
def start_gui():
    global custom_text_entry, user_id_entry, webhook_url_entry, screenshot_delay_entry, dark_mode_var

    root = ctk.CTk()
    root.title("Aegis Screenshot Assistor")

    
    ctk.CTkLabel(root, text="Custom Text:").grid(row=0, column=0, padx=10, pady=10)
    custom_text_entry = ctk.CTkEntry(root, width=50)
    custom_text_entry.grid(row=0, column=1, padx=10, pady=10)
    custom_text_entry.insert(0, custom_text)

    
    ctk.CTkLabel(root, text="User ID (for ping):").grid(row=1, column=0, padx=10, pady=10)
    user_id_entry = ctk.CTkEntry(root, width=50)
    user_id_entry.grid(row=1, column=1, padx=10, pady=10)
    user_id_entry.insert(0, user_id)

   
    ctk.CTkLabel(root, text="Webhook URL:").grid(row=2, column=0, padx=10, pady=10)
    webhook_url_entry = ctk.CTkEntry(root, width=50)
    webhook_url_entry.grid(row=2, column=1, padx=10, pady=10)
    webhook_url_entry.insert(0, WEBHOOK_URL)


    ctk.CTkLabel(root, text="Screenshot Delay (seconds):").grid(row=3, column=0, padx=10, pady=10)
    screenshot_delay_entry = ctk.CTkEntry(root, width=50)
    screenshot_delay_entry.grid(row=3, column=1, padx=10, pady=10)
    screenshot_delay_entry.insert(0, str(screenshot_delay))

   
    dark_mode_var = ctk.BooleanVar(value=dark_mode)
    dark_mode_checkbox = ctk.CTkCheckBox(root, text="Enable Dark Mode", variable=dark_mode_var)
    dark_mode_checkbox.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

   
    update_button = ctk.CTkButton(root, text="Update Settings", command=update_settings)
    update_button.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

    
    gif_button = ctk.CTkButton(root, text="Select GIF", command=select_gif)
    gif_button.grid(row=6, column=0, columnspan=2, padx=10, pady=10)

    
    start_button = ctk.CTkButton(root, text="Start Capturing", command=on_start_capture)
    start_button.grid(row=7, column=0, columnspan=2, padx=10, pady=10)

    
    stop_button = ctk.CTkButton(root, text="Stop Capturing", command=on_stop_capture)
    stop_button.grid(row=8, column=0, columnspan=2, padx=10, pady=10)

    
    credits_button = ctk.CTkButton(root, text="Credits", command=show_credits)
    credits_button.grid(row=9, column=0, columnspan=2, padx=10, pady=10)

    root.protocol("WM_DELETE_WINDOW", lambda: root.quit())
    root.mainloop()

if __name__ == "__main__":
    start_gui()

