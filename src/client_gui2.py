# ################ A simple graphical interface which communicates with the server #####################################

# while client_gui only allows to set the facelets with the mouse, this file (client_gui2) also takes input from the
# webcam and includes sliders for some opencv parameters

from tkinter import *
import socket
import face
import cubie
from threading import Thread
from vision2 import grab_colors
import vision_params
import serial
from serial import serialutil
import platform
import codecs


import numpy as np

# ################################## some global variables and constants ###############################################
DEFAULT_HOST = 'localhost'
DEFAULT_PORT = '8080'
com_ports = {'Darwin': '/dev/ttyUSB0',
             'Linux': '/dev/ttyUSB0',
             'Windows': 'COM6'}
baudrate = 9600
os = platform.system()

width = 60  # width of a facelet in pixels
facelet_id = [[[0 for col in range(3)] for row in range(3)] for fc in range(6)]
colorpick_id = [0 for i in range(6)]
curcol = None
t = ("U", "R", "F", "D", "L", "B")
cols = ("white", "red", "green", "yellow", "orange", "blue")
solution = ''

########################################################################################################################

# ############################################# Serial functions #######################################################


class nonloc:
    pass


def send_serial():
    message = decode(nonloc.solution)
    hexlify = codecs.getencoder('hex')
    hex_message = hexlify(message.encode())[0]
    print(message)
    print(hex_message)
    display.delete(1.0, END)
    ser = serial.Serial()
    ser.baudrate = baudrate
    ser.port = com_ports[os]
    try:
        ser.open()
        print('Serial connection opened')
        ser.write(message.encode())
        show_text('Solution sent')
    except serialutil.SerialTimeoutException:
        show_text('Serial timeout')
    except serialutil.SerialException:
        show_text('Serial connection could not be opened')


    if ser.is_open:
        ser.close()


def decode(solution):
    decode_dict = {'R1': 'A',
                   'R3': 'B',
                   'R2': 'C',
                   'L1': 'D',
                   'L3': 'E',
                   'L2': 'F',
                   'U1': 'G',
                   'U3': 'H',
                   'U2': 'I',
                   'D1': 'J',
                   'D3': 'K',
                   'D2': 'L',
                   'F1': 'M',
                   'F3': 'N',
                   'F2': 'O',
                   'B1': 'P',
                   'B3': 'Q',
                   'B2': 'R'}

    sol_list = solution.split(' ')
    output = ''
    del sol_list[-1]
    for move in sol_list:
        output += decode_dict[move]
    return output

########################################################################################################################

# ################################################ Diverse functions ###################################################


def show_text(txt):
    """Displays messages."""
    print(txt)
    display.insert(INSERT, txt)
    root.update_idletasks()


def create_facelet_rects(a):
    """Initializes the facelet grid on the canvas."""
    offset = ((1, 0), (2, 1), (1, 1), (1, 2), (0, 1), (3, 1))
    for f in range(6):
        for row in range(3):
            y = 10 + offset[f][1] * 3 * a + row * a
            for col in range(3):
                x = 10 + offset[f][0] * 3 * a + col * a
                facelet_id[f][row][col] = canvas.create_rectangle(x, y, x + a, y + a, fill="grey")
                if row == 1 and col == 1:
                    canvas.create_text(x + width // 2, y + width // 2, font=("", 14), text=t[f], state=DISABLED)
    for f in range(6):
        canvas.itemconfig(facelet_id[f][1][1], fill=cols[f])


def create_colorpick_rects(a):
    """Initializes the "paintbox" on the canvas"""
    global curcol
    global cols
    for i in range(6):
        x = (i % 3) * (a + 5) + 7 * a
        y = (i // 3) * (a + 5) + 7 * a
        colorpick_id[i] = canvas.create_rectangle(x, y, x + a, y + a, fill=cols[i])
        canvas.itemconfig(colorpick_id[0], width=4)
        curcol = cols[0]


def get_definition_string():
    """Generates the cube definition string from the facelet colors."""
    color_to_facelet = {}
    for i in range(6):
        color_to_facelet.update({canvas.itemcget(facelet_id[i][1][1], "fill"): t[i]})
    s = ''
    for f in range(6):
        for row in range(3):
            for col in range(3):
                s += color_to_facelet[canvas.itemcget(facelet_id[f][row][col], "fill")]
    return s


########################################################################################################################

# ############################### Solve the displayed cube with a local or remote server ###############################


def solve():
    """Connects to the server and returns the solving maneuver."""
    display.delete(1.0, END)  # clear output window
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        show_text('Failed to create socket')
        return
    # host = 'f9f0b2jt6zmzyo6b.myfritz.net'  # my RaspberryPi, if online
    host = txt_host.get(1.0, END).rstrip()  # default is localhost
    port = int(txt_port.get(1.0, END))  # default is port 8080

    try:
        remote_ip = socket.gethostbyname(host)
    except socket.gaierror:
        show_text('Hostname could not be resolved.')
        return
    try:
        s.connect((remote_ip, port))
    except:
        show_text('Cannot connect to server!')
        return
    show_text('Connected with ' + remote_ip + '\n')
    try:
        defstr = get_definition_string() + '\n'
    except:
        show_text('Invalid facelet configuration.\nWrong or missing colors.')
        return
    show_text(defstr)
    try:
        s.sendall((defstr + '\n').encode())
    except:
        show_text('Cannot send cube configuration to server.')
        return

    nonloc.solution = s.recv(2048).decode()
    show_text(nonloc.solution)
    bsend.config(state='normal')


########################################################################################################################

# ################################# Functions to change the facelet colors #############################################


def clean():
    """Restores the cube to a clean cube."""
    for f in range(6):
        for row in range(3):
            for col in range(3):
                canvas.itemconfig(facelet_id[f][row][col], fill=canvas.itemcget(facelet_id[f][1][1], "fill"))
    bsend.config(state=DISABLED)


def empty():
    """Removes the facelet colors except the center facelets colors."""
    for f in range(6):
        for row in range(3):
            for col in range(3):
                if row != 1 or col != 1:
                    canvas.itemconfig(facelet_id[f][row][col], fill="grey")
    bsend.config(state=DISABLED)


def random():
    """Generates a random cube and sets the corresponding facelet colors."""
    cc = cubie.CubieCube()
    cc.randomize()
    fc = cc.to_facelet_cube()
    idx = 0
    for f in range(6):
        for row in range(3):
            for col in range(3):
                canvas.itemconfig(facelet_id[f][row][col], fill=cols[fc.f[idx]])
                idx += 1
    bsend.config(state=DISABLED)


########################################################################################################################

# ################################### Edit the facelet colors ##########################################################


def click(event):
    """Defines how to react on left mouse clicks"""
    global curcol
    idlist = canvas.find_withtag("current")
    if len(idlist) > 0:
        if idlist[0] in colorpick_id:
            curcol = canvas.itemcget("current", "fill")
            for i in range(6):
                canvas.itemconfig(colorpick_id[i], width=1)
            canvas.itemconfig("current", width=5)
        else:
            canvas.itemconfig("current", fill=curcol)


########################################################################################################################


# ######################################### functions to set the slider values #########################################
def set_rgb_L(val):
    vision_params.rgb_L = int(val)


def set_orange_L(val):
    vision_params.orange_L = int(val)


def set_orange_H(val):
    vision_params.orange_H = int(val)


def set_yellow_H(val):
    vision_params.yellow_H = int(val)


def set_green_H(val):
    vision_params.green_H = int(val)


def set_blue_H(val):
    vision_params.blue_H = int(val)


def set_sat_W(val):
    vision_params.sat_W = int(val)


def set_val_W(val):
    vision_params.val_W = int(val)


def set_sigma_C(val):
    vision_params.sigma_C = int(val)


def set_delta_C(val):
    vision_params.delta_C = int(val)


def transfer():
    """ Transfer the facelet colors detected by the opencv vision to the GUI editor """
    if len(vision_params.face_col) == 0:
        return
    centercol = vision_params.face_col[1][1]

    vision_params.cube_col[centercol] = vision_params.face_col
    vision_params.cube_hsv[centercol] = vision_params.face_hsv

    dc = {}
    for i in range(6):
        dc[canvas.itemcget(facelet_id[i][1][1], "fill")] = i  # map color to face number
    for i in range(3):
        for j in range(3):
            canvas.itemconfig(facelet_id[dc[centercol]][i][j], fill=vision_params.face_col[i][j])

# ######################################################################################################################

#  ###################################### Generate and display the TK_widgets ##########################################

root = Tk()
root.wm_title("Solver Client")
canvas = Canvas(root, width=12 * width + 20, height=9 * width + 20)
canvas.pack()

bsolve = Button(text="Solve", height=1, width=10, relief=RAISED, command=solve)
bsolve_window = canvas.create_window(10 + 10.5 * width, 10 + 6.5 * width, anchor=NW, window=bsolve)
bclean = Button(text="Clean", height=1, width=10, relief=RAISED, command=clean)
bclean_window = canvas.create_window(10 + 10.5 * width, 10 + 7 * width, anchor=NW, window=bclean)
bempty = Button(text="Empty", height=1, width=10, relief=RAISED, command=empty)
bempty_window = canvas.create_window(10 + 10.5 * width, 10 + 7.5 * width, anchor=NW, window=bempty)
brandom = Button(text="Random", height=1, width=10, relief=RAISED, command=random)
brandom_window = canvas.create_window(10 + 10.5 * width, 10 + 8 * width, anchor=NW, window=brandom)
bsend = Button(text='Send', height=1, width=10, relief=RAISED, command=lambda: send_serial(),
               state=DISABLED)
bsend_window = canvas.create_window(10 + 10.5 * width, 10 + 8.5 * width, anchor=NW, window=bsend)
display = Text(height=7, width=39)
text_window = canvas.create_window(10 + 6.5 * width, 10 + .5 * width, anchor=NW, window=display)
hp = Label(text='    Hostname and Port')
hp_window = canvas.create_window(10 + 0 * width, 10 + 0.6 * width, anchor=NW, window=hp)
txt_host = Text(height=1, width=20)
txt_host_window = canvas.create_window(10 + 0 * width, 10 + 1 * width, anchor=NW, window=txt_host)
txt_host.insert(INSERT, DEFAULT_HOST)
txt_port = Text(height=1, width=20)
txt_port_window = canvas.create_window(10 + 0 * width, 10 + 1.5 * width, anchor=NW, window=txt_port)
txt_port.insert(INSERT, DEFAULT_PORT)
canvas.bind("<Button-1>", click)
create_facelet_rects(width)
create_colorpick_rects(width)

s_orange_L = Scale(root, from_=1, to=14, length=width * 1.4, showvalue=0, label='red-orange', orient=HORIZONTAL,
                   command=set_orange_L)
canvas.create_window(10, 12 + 6.0 * width, anchor=NW, window=s_orange_L)
s_orange_L.set(vision_params.orange_L)

s_orange_H = Scale(root, from_=8, to=40, length=width * 1.4, showvalue=0, label='orange-yellow', orient=HORIZONTAL,
                   command=set_orange_H)
canvas.create_window(10, 12 + 6.6 * width, anchor=NW, window=s_orange_H)
s_orange_H.set(vision_params.orange_H)

s_yellow_H = Scale(root, from_=31, to=80, length=width * 1.4, showvalue=0, label='yellow-green', orient=HORIZONTAL,
                   command=set_yellow_H)
canvas.create_window(10, 12 + 7.2 * width, anchor=NW, window=s_yellow_H)
s_yellow_H.set(vision_params.yellow_H)

s_green_H = Scale(root, from_=70, to=120, length=width * 1.4, showvalue=0, label='green-blue', orient=HORIZONTAL,
                  command=set_green_H)
canvas.create_window(10, 12 + 7.8 * width, anchor=NW, window=s_green_H)
s_green_H.set(vision_params.green_H)

s_blue_H = Scale(root, from_=120, to=180, length=width * 1.4, showvalue=0, label='blue-red', orient=HORIZONTAL,
                 command=set_blue_H)
canvas.create_window(10, 12 + 8.4 * width, anchor=NW, window=s_blue_H)
s_blue_H.set(vision_params.blue_H)

s_rgb_L = Scale(root, from_=0, to=140, length=width * 1.4, showvalue=0, label='black-filter', orient=HORIZONTAL,
                command=set_rgb_L)
canvas.create_window(10 + width * 1.5, 12 + 6 * width, anchor=NW, window=s_rgb_L)
s_rgb_L.set(vision_params.rgb_L)

s_sat_W = Scale(root, from_=120, to=0, length=width * 1.4, showvalue=0, label='white-filter s', orient=HORIZONTAL,
                command=set_sat_W)
canvas.create_window(10 + width * 1.5, 12 + 6.6 * width, anchor=NW, window=s_sat_W)
s_sat_W.set(vision_params.sat_W)

s_val_W = Scale(root, from_=80, to=255, length=width * 1.4, showvalue=0, label='white-filter v', orient=HORIZONTAL,
                command=set_val_W)
canvas.create_window(10 + width * 1.5, 12 + 7.2 * width, anchor=NW, window=s_val_W)
s_val_W.set(vision_params.val_W)

s_sigma_C = Scale(root, from_=30, to=0, length=width * 1.4, showvalue=0, label='color-filter \u03c3', orient=HORIZONTAL,
                  command=set_sigma_C)
canvas.create_window(10 + width * 1.5, 12 + 7.8 * width, anchor=NW, window=s_sigma_C)
s_sigma_C.set(vision_params.sigma_C)

s_delta_C = Scale(root, from_=10, to=0, length=width * 1.4, showvalue=0, label='color-filter \u03b4', orient=HORIZONTAL,
                  command=set_delta_C)
canvas.create_window(10 + width * 1.5, 12 + 8.4 * width, anchor=NW, window=s_delta_C)
s_delta_C.set(vision_params.delta_C)

btransfer = Button(text="Webcam import", height=2, width=13, relief=RAISED, command=transfer)
canvas.create_window(10 + 0.5 * width, 10 + 2.1 * width, anchor=NW, window=btransfer)


root.mainloop()

########################################################################################################################
