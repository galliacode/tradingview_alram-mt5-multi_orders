import threading
import time
from selenium import webdriver
import json
from selenium.webdriver.common.by import By
from datetime import datetime
import requests
import tkinter as tk
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime, timedelta

driver = webdriver.Chrome()
driver.get("https://tradingview.com/")
startTime = datetime.now()

def load_session_id():
    try:
        with open("session_id.json", "r") as file:
            data = json.load(file)
            return data.get("session_id", "")
    except FileNotFoundError:
        return ""


def save_session_id():
    session_id.set(entry.get())
    with open("session_id.json", "w") as file:
        json.dump({"session_id": session_id}, file)
    print("Session ID saved successfully.")


# Define your cookie
cookie = {
    'name': 'sessionid',
    'value': load_session_id(),
    'path': '/',
    'domain': '.tradingview.com',  # Change to the domain of the website
    'secure': True,
    'httpOnly': True
}

driver.add_cookie(cookie)

driver.get("https://tradingview.com/markets/currencies/rates-all/")
alert_list = []

# element_list = []
alive = True


def load_session_id():
    try:
        with open("session_id.json", "r") as file:
            data = json.load(file)
            return data.get("session_id", "")
    except FileNotFoundError:
        return ""


def save_session_id():
    session_id.set(entry.get())
    with open("session_id.json", "w") as file:
        json.dump({"session_id": session_id}, file)
    print("Session ID saved successfully.")


def process_browser_log_entry(entry):
    response = json.loads(entry['message'])['message']
    return response


# Define the server URL where you want to send the data
server_url = 'http://localhost:5000/receive_data'


def monitor_requests():
    global alert_list
    # global element_list
    try:
        while True and alive:
            # Process requests that have been captured
            alert = None
            if datetime.now() - startTime == timedelta(hours=3):
                quit(0)

            try:
                closer = driver.find_element(By.CLASS_NAME, "close-OuOkx1rR")
                closer.click()
            except:
                pass
            try:
                alert = driver.find_element(By.CLASS_NAME, 'message-PQUvhamm')
            except:
                pass
            if alert:
                try:
                    message = alert.text
                    elements = message.split("\n")

                    parent = alert.parent
                    for entry in entry_list:
                        print(f"Trying ELEMENT -> {elements} for PORT : {entry}")
                        response = requests.post(f"http://127.0.0.1:{entry}/receive_data", data={'data': elements})
                        # Check the response from the server
                        if response.status_code == 200:
                            print("Data sent to server successfully.")
                            while True and alive:
                                try:
                                    close_button = parent.find_element(By.XPATH,
                                                                       "/html/body/div[2]/div/div[2]/div[1]/div[2]/div[2]/div[2]/div/div[2]/div[2]/div[4]/div")
                                    hover = ActionChains(driver).move_to_element(close_button)
                                    hover.perform()
                                    close_button.click()
                                except:
                                    print("No more alerts left")
                                else:
                                    break
                        else:
                            print("Error sending data to server:", response.status_code)
                except:
                    pass
            else:
                pass
            try:
                button = driver.find_element(By.XPATH,
                                             "/html/body/div[6]/div[2]/div/div[2]/div/div/div[1]/div/div/div/div[3]/div/button[1]")
                button.click()
            except Exception as e:
                pass

    except KeyboardInterrupt:
        print("Stopping monitoring...")


# Run the monitoring in a background thread
thread = threading.Thread(target=monitor_requests)
thread.start()

# Create main window
root = tk.Tk()
root.title("Client")
root.geometry("300x350")

session_id = tk.StringVar()

# Entry field for session ID
entry = tk.Entry(root)
entry.insert(0, session_id.get())
entry.pack(pady=10)

# Button to save session ID
button = tk.Button(root, text="Save Session ID", command=save_session_id)
button.pack()

default_value = 5001
entry_list = [str(default_value)]


def add_entry():
    global default_value
    if default_value == 5004:
        return
    default_value += 1
    entry_list.append(str(default_value))
    update_listbox()


def update_listbox():
    listbox.delete(0, tk.END)
    for entry in entry_list:
        listbox.insert(tk.END, entry)


tk.Label(text="Ports").pack()
# Create listbox to display entries
listbox = tk.Listbox(root)
listbox.pack(pady=10)

add_button = tk.Button(root, text="Add Entry", command=add_entry)
add_button.pack()

# Add initial entry
update_listbox()

print("Monitoring started. Press Ctrl+C to stop.")
try:
    root.mainloop()
except KeyboardInterrupt:
    print("Stopping script...")
    alive = False

alive = False

# Cleanup
driver.quit()
