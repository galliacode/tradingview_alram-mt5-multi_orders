import threading
import flask
from flask import Flask, request, jsonify
import MetaTrader5 as mt5
import re
import tkinter as tk
from tkinter import filedialog
from datetime import datetime, timedelta
import numpy
import pandas

name = 'main'
app = Flask(name)

comment_list = []

# Initialize MetaTrader 5 connection
if not mt5.initialize(path='t4/terminal64.exe'):
    print("Initialize() failed, error code =", mt5.last_error())
    quit()


@app.route('/receive_data', methods=['POST'])
def receive_data():
    data_str = request.form['data']
    data_arr = data_str.split(',')
    print(f"Received data: {data_arr}")
    print("Data Type", type(data_arr))

    # Here you can process the data and make orders with MT5 based on your strategy
    # For demonstration, we'll just log the data received
    process_data_and_place_order(data_arr)

    return jsonify({'status': 'success', 'message': 'Data received'}), 200


def process_data_and_place_order(data):
    global reverse, extracted_text, use_file, lot_dict
    # Parse the data
    # Example: parsed_data = parse_data(data)

    # Check if MT5 terminal is connected
    if not mt5.terminal_info():
        print("MT5 terminal is not connected")
        return

    symbol = data[0].strip()
    print(symbol)
    if symbol in sym_dict and use_conv.get():
        # Replace the variable with its corresponding value
        symbol = result_dict[symbol]

    selected = mt5.symbol_select(symbol, True)
    if not selected:
        print("Failed to select " + symbol)
        return

    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(symbol, "not found, can not call order_check()")
        return

    # if the symbol is unavailable in MarketWatch, add it
    if not symbol_info.visible:
        print(symbol, "is not visible, trying to switch on")
        if not mt5.symbol_select(symbol, True):
            print("symbol_select({}}) failed, exit", symbol)
            return

    lot = 0.1
    if symbol in lot_dict and use_lot.get():
        lot = float(lot_dict[symbol])
    tick = mt5.symbol_info_tick(symbol)
    print(tick)
    point = tick.bid
    price = tick.ask
    print(price)
    order_type = 0 if data[1].strip() == "buy" else 1

    # Reverse the order type based on the option
    if reverse.get():
        order_type = 1 if order_type == 0 else 0

    sl = round(price - (0.01 * price), 5) if order_type == 0 else round(point + (0.01 * price), 5)
    tp = round(price + (0.01 * price), 5) if order_type == 0 else round(point - (0.01 * price), 5)
    print(f"Lot size = {lot}")
    print("Stop Loss = " + str(sl))
    print("Take Profit = " + str(tp))
    print("Order type : " + str(order_type))

    comment = re.split('=', data[5].strip(), maxsplit=1)[1]
    start = 0
    end = 0
    if len(data) == 7:
        timeframe = re.split('=', data[6].strip(), maxsplit=1)[1]
        start = re.split('-', timeframe, maxsplit=1)[0]
        end = re.split('-', timeframe, maxsplit=1)[1]

    ret_logic = True
    comment_list = []

    # Now we get all positions from the Terminal
    positions = mt5.positions_get(symbol=symbol)

    # Now extract the list of comments
    if positions:
        comment_list = [pos.comment for pos in positions]
    print(comment_list)
    if comment in comment_list:
        if positions:
            print(positions)
            for pos in positions:
                if comment == pos.comment:
                    ticket = pos.ticket
                    if pos.type == order_type:
                        print("---------\nOrder with same comment AND order type is present\n---------")
                        return
                    print("Going to close this existing order with ticket " + str(ticket) + " and symbol: " + symbol)
                    mt5.Close(symbol=symbol, ticket=ticket)
                    print("Removed the order")
                    if len(data) == 7:
                        print("Proceeding to check for ET conditions")
                        order_time = datetime.fromtimestamp(pos.time)
                        # time = pandas.DataFrame({'time':[order_time]})
                        # time['time'] = pandas.to_datetime(time['time'], unit='s')

                        current_time = datetime.now()
                        print(f"Order Time = {order_time}")
                        print(f"Current Time = {current_time}")
                        delta = current_time - order_time + timedelta(hours=3)
                        print(f"Delta time = {delta}")
                        start = timedelta(hours=int(start))
                        end = timedelta(hours=int(end))
                        print(f"Start Delta = {start}")
                        print(f"End Delta = {end}")
                        if start < delta < end or start == end:
                            ret_logic = False
                            print("Order to be reversed")
                    if ret_logic:
                        comment_list.remove(comment)
                        return
        if ret_logic:
            print("Order with same comment is present")
            return

    if extracted_text and use_file.get():
        if comment in extracted_text:
            pass
        else:
            print("Not found in provided list")
            return

    risk = int(re.split('=', data[3].strip(), maxsplit=1)[1])
    magic = int(re.split('=', data[4].strip(), maxsplit=1)[1])
    print("Comment = " + comment)
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": price if order_type == 0 else point,
        "sl": sl,
        "tp": tp,
        "magic": magic,
        "risk": risk,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)  # Error here
    print(result)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("Failed to send order :(", result.retcode)
    else:
        print("Order placed successfully!")

    # Implement your own logic here based on the data
    pass


def start_server():
    app.run(debug=False, port=5003, threaded=True)


extracted_text = []
sym_dict = {}
lot_dict = {}
server_thread = threading.Thread(target=start_server)
server_thread.start()

# Setting up the GUI using Tkinter

# Create main window
root = tk.Tk()
title = tk.StringVar()
account = mt5.account_info()
title.set(f"Alert Bridge : {account.login}|{account.name}|{account.server}")
root.title(title.get())
root.geometry("350x400")
root.grid()

# Create a Checkbutton widget
reverse = tk.BooleanVar()
reverse.set(False)
check_button = tk.Checkbutton(root, text="Reverse", variable=reverse)
check_button.pack()


def browse_file():
    global extracted_text
    filename = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if filename:
        with open(filename, 'r') as file:
            text = file.read()
            extracted_text = [s.strip() for s in text.split(',')]
            display_text.config(text=f"Comments : {extracted_text}")


def browse_file_sym():
    global sym_dict
    filename = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if filename:
        with open(filename, 'r') as file:
            text = file.read()
            extracted_text_sym = [s.strip() for s in text.split(',')]
            sym_dict = dict(item.split('=') for item in extracted_text_sym)
            display_text_sym.config(text=f"{sym_dict}")


def browse_file_lot():
    global lot_dict
    filename = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if filename:
        with open(filename, 'r') as file:
            text = file.read()
            extracted_text_sym = [s.strip() for s in text.split(',')]
            lot_dict = dict(item.split('=') for item in extracted_text_sym)
            display_text_lot.config(text=f"{lot_dict}")


# Creating a button to browse for a file
browse_button = tk.Button(root, text="Browse File", command=browse_file)
browse_button.pack(pady=10)

# Create a Checkbutton widget for comments file
use_file = tk.BooleanVar()
use_file.set(False)
check_button_comment = tk.Checkbutton(root, text="Use Comments File", variable=use_file)
check_button_comment.pack()

# Label to display the extracted text
display_text = tk.Label(root, text="")
display_text.pack(pady=10)

# Creating a button to browse for a file
browse_button_sym = tk.Button(root, text="Select Symbol File", command=browse_file_sym)
browse_button_sym.pack(pady=10)

# Create a Checkbutton widget for Symbols Conversion file
use_conv = tk.BooleanVar()
use_conv.set(False)
check_button_conv = tk.Checkbutton(root, text="Use Conversion File", variable=use_conv)
check_button_conv.pack()

# Label to display the extracted text
display_text_sym = tk.Label(root, text="")
display_text_sym.pack(pady=10)

# Creating a button to browse for a file
browse_button_lot = tk.Button(root, text="Select Lot File", command=browse_file_lot)
browse_button_lot.pack(pady=10)

# Create a Checkbutton widget for Lot setting file
use_lot = tk.BooleanVar()
use_lot.set(True)
check_button_lot = tk.Checkbutton(root, text="Use Lot File", variable=use_lot)
check_button_lot.pack()

# Label to display the extracted text
display_text_lot = tk.Label(root, text="")
display_text_lot.pack(pady=10)

# Run the Tkinter event loop
root.mainloop()
