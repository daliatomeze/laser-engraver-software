import time
from cgitb import text
from xml.dom import minidom
import cv2
import matplotlib.pyplot as plt
import numpy as np
import svgpathtools
import svgwrite
from setuptools._distutils.command.clean import clean
from svgpathtools import svg2paths
from tsp_solver.greedy_numpy import solve_tsp
import turtle


####################################################
def resize_image(image_path1, scale_percent):
    # Load the image
    image = cv2.imread(image_path1)
    # Get the original image dimensions
    height, width = image.shape[:2]
    # Calculate the new image dimensions based on the scale percent
    new_width = int(width * scale_percent / 100)
    new_height = int(height * scale_percent / 100)
    # Resize the image
    resized_image = cv2.resize(image, (new_width, new_height))
    # Return the resized image
    return resized_image


####################################################
def edited_image(img):
    # Convert to grayscale and apply edge detection
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #set thresold value by input it by user 128 initial
    thresold2 = 127
    ret, thresh = cv2.threshold(gray, thresold2, 255, cv2.THRESH_BINARY)

    edges = cv2.Canny(thresh, 100, 200)
    # Find the contours of the edges
    #initial RETR_CCOMP
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    return contours
####################################################

def svgtolines(paths, attributes):
    lines = []
    for path in paths:
        for segment in path:
            if isinstance(segment, svgpathtools.Line):
                start = segment.start * 1
                end = segment.end * 1
                lines.append(svgpathtools.Line(start, end))
            elif isinstance(segment, svgpathtools.CubicBezier):
                lines += segment.to_lines()
            elif isinstance(segment, svgpathtools.Arc):
                lines += segment.approximate(max(1, int(segment.length() / 10)))
    return lines



def optimize_line(lines):
    # Optimize line segments for minimum travel distance
    distances = np.zeros((len(lines), len(lines)))
    for i in range(len(lines)):
        for j in range(len(lines)):
            if i != j:
                distances[i][j] = abs(lines[i].end - lines[j].start)
    return distances


####################################################


####################################################


"""def gcode_generator(optimized_lines, laser_speed,laser_power, svg_dimensions):

    # Initialize serial port for GRBL
    # Generate G-code
    gcode = []
    gcode.append("; G-code generated from input.svg")
    # Set units to millimeters
    gcode.append("G21")
    # Set absolute coordinates
    gcode.append("G90")
    # Set speed
    gcode.append("F{}".format(laser_speed))
    # Calculate scale factor based on SVG dimensions
    svg_width, svg_height = svg_dimensions
    gcode_width, gcode_height = svg_width, svg_height  # initial values
    # Move to starting position without turning on the laser
    gcode.append("G0 X{} Y{} Z{}".format(optimized_lines[0].start.real, optimized_lines[0].start.imag, 0))
    # Wait for the movement to complete
    while True:
        ser.write(b"?")
        response = ser.readline().strip().decode("utf-8")
        if "Idle" in response:
            break
    # or this
    # gcode.append( "G0 X{} Y{} Z{}\n".format(gcode_width / 2, gcode_height / 2, 0))
    # Initialize is_laser_on
    is_laser_on = False
    print(canvas_height)
    print(canvas_width)
    width_scale_factor = (canvas_width*0.02)/gcode_width
    height_scale_factor = (canvas_height*0.02)/gcode_height
    # Set up turtle to draw on canvas
    turtle_screen = turtle.TurtleScreen(canvas)
    turtle_screen.setworldcoordinates(0, 0, (canvas_width*0.02*width_scale_factor)+8.19, 4.6+(canvas_height*0.02*height_scale_factor))
    #turtle_screen.delay(0)
    turtle_screen.bgcolor("#333333")
    # Set up turtle to draw with a pen
    turtle_pen = turtle.RawTurtle(turtle_screen)
    turtle_pen.penup()
    turtle_pen.speed(0)
    turtle_pen.color("red")
    turtle_pen.width(4)
    ---comment---
    sum = 6 #for printing gcode in step3
    for sum,line in enumerate(optimized_lines):
        # Turn off the laser if it was on
        if is_laser_on:
            gcode += "M5\n"
            is_laser_on = False
        x = [line.start.real, line.end.real]
        y = [line.start.imag, line.end.imag]
        # Move to the start of the line
        gcode += "G0 X{} Y{} Z{}\n".format(x[0], gcode_height - y[0], 0)

        # Turn on the laser
        gcode += "M3 S{}\n".format(laser_power)
        is_laser_on = True

        # Move to the end of the line with laser on
        gcode += "G1 X{} Y{} Z{}\n".format(x[1], gcode_height - y[1], 0)
        ser.write(gcode.encode('utf-8'))
        turtle_pen.penup()
        turtle_pen.goto(x[0], gcode_height - y[0])
        turtle_pen.pendown()
        turtle_pen.goto(x[1], gcode_height - y[1])
        gcode = ""
        sum = sum + 1
        # Wait for the movement to complete
        while True:
            ser.write(b"?")
            response = ser.readline().strip().decode("utf-8")
            if "Idle" in response:
                break
        ---comment---

    i=6
    for i in range(len(optimized_lines)):
        line = optimized_lines[i]

        # Turn off the laser
        gcode.append("M05")
        ser.write(b"M05\n")

        # Move to the start of the line
        gcode.append("G0 X{} Y{} Z{}".format(line.start.real, gcode_height - line.start.imag, 0))
        ser.write("G0 X{} Y{} Z{}\n".format(line.start.real, gcode_height - line.start.imag, 0).encode())

        # Turn on the laser
        gcode.append("M03 S{}".format(laser_power))
        ser.write("M03 S{}\n".format(laser_power).encode())

        # Move along the line
        for j in range(len(line)):
            point = line[j]

            # Move to the next point
            gcode.append("G1 X{} Y{} Z{}".format(point.real, gcode_height - point.imag, 0))
            ser.write("G1 X{} Y{} Z{}\n".format(point.real, gcode_height - point.imag, 0).encode())

            # Wait for the movement to complete
            while True:
                ser.write(b"?")
                response = ser.readline().strip().decode("utf-8")
                if "Idle" in response:
                    break

        # Turn off the laser
        gcode.append("M05")
        ser.write(b"M05\n")

        turtle_pen.penup()
        turtle_pen.goto(line.start.real, gcode_height - line.start.imag)
        turtle_pen.pendown()
        for j in range(len(line)):
            point = line[j]
            turtle_pen.goto(point.real, gcode_height - point.imag)
    if is_laser_on:
        gcode += "M5\n"
        is_laser_on = False

    # Turn off the laser and move to the origin
    gcode += "S0\n"
    gcode += "M5\n"
    gcode += "G0 X{} Y{} Z{}\n".format(0, 0, 0)
    # Send G-code to GRBL
    ser.write(gcode.encode('utf-8'))"""

#For Test
def gcode_generator(optimized_lines, laser_speed,laser_power, svg_dimensions):
    # Open serial port
    # Calculate scale factor based on SVG dimensions
    svg_width, svg_height = svg_dimensions
    gcode_width, gcode_height = svg_width, svg_height  # initial values
    # Wait for the serial connection to be established
    time.sleep(2)
    # Generate G-code
    gcode = []
    gcode.append("; G-code generated from input.svg")
    # Set units to millimeters
    gcode.append("G21")
    ser.write(b"G21\n")
    # Set absolute coordinates
    gcode.append("G90")
    ser.write(b"G90\n")

    # Set speed
    gcode.append("F{}".format(laser_speed))
    ser.write("F{}\n".format(laser_speed).encode())
    # Move to starting position without turning on the laser
    gcode.append("G0 X{} Y{} Z{}".format(optimized_lines[0].start.real, optimized_lines[0].start.imag, 0))
    ser.write("G0 X{} Y{} Z{}\n".format(optimized_lines[0].start.real, optimized_lines[0].start.imag, 0).encode())
    # Move to starting position without turning on the laser
    #gcode.append("G0 X{} Y{} Z{}\n".format(gcode_width / 2, gcode_height / 2, 0,laser_speed))
    #ser.write("G0 X{} Y{} Z{}\n".format(gcode_width / 2, gcode_height / 2, 0).encode())
    # Wait for the movement to complete
    while True:
        ser.write(b"?")
        response = ser.readline().strip().decode("utf-8")
        if "Idle" in response:
            break
    # Initialize is_laser_on
    is_laser_on = False
    print(canvas_height)
    print(canvas_width)
    width_scale_factor = (canvas_width*0.02)/gcode_width
    height_scale_factor = (canvas_height*0.02)/gcode_height
    # Set up turtle to draw on canvas
    turtle_screen = turtle.TurtleScreen(canvas)
    turtle_screen.setworldcoordinates(8.19, 4.6, (canvas_width*0.02*width_scale_factor)+8.19, 4.6+(canvas_height*0.02*height_scale_factor))
    #turtle_screen.delay(0)
    turtle_screen.bgcolor("#333333")
    # Set up turtle to draw with a pen
    turtle_pen = turtle.RawTurtle(turtle_screen)
    turtle_pen.penup()
    turtle_pen.speed(0)
    sum = 6 #for printing gcode in step3
    # Send each G-code command to the GRBL controller
    for i in range(len(optimized_lines)):
        line = optimized_lines[i]

        # Turn off the laser
        gcode.append("M05")
        ser.write(b"M05\n")

        # Move to the start of the line
        gcode.append("G0 X{} Y{} Z{}".format(line.start.real, gcode_height - line.start.imag, 0))
        ser.write("G0 X{} Y{} Z{}\n".format(line.start.real, gcode_height - line.start.imag, 0).encode())

        # Turn on the laser
        gcode.append("M03 S{}".format(laser_power))
        ser.write("M03 S{}\n".format(laser_power).encode())

        # Move along the line
        for j in range(len(line)):
            point = line[j]

            # Move to the next point
            gcode.append("G1 X{} Y{} Z{}".format(point.real, gcode_height - point.imag, 0))
            ser.write("G1 X{} Y{} Z{}\n".format(point.real, gcode_height - point.imag, 0).encode())

            # Wait for the movement to complete
            while True:
                ser.write(b"?")
                response = ser.readline().strip().decode("utf-8")
                if "Idle" in response:
                    break

        # Turn off the laser
        gcode.append("M05")
        ser.write(b"M05\n")

        turtle_pen.penup()
        turtle_pen.goto(line.start.real, gcode_height - line.start.imag)
        turtle_pen.pendown()
        for j in range(len(line)):
            point = line[j]
            turtle_pen.goto(point.real, gcode_height - point.imag)
        print(gcode[i])
    if is_laser_on:
        gcode.append("M05")
        is_laser_on = False

    # Turn off the laser and move to the origin
    gcode.append("S0")
    ser.write(b"S0\n")

    gcode.append("M05")
    ser.write(b"M05\n")

    gcode.append("G0 X{} Y{} Z{}\n".format(0, 0, 0,laser_speed))
    ser.write("G0 X{} Y{} Z{}\n".format(0,0, 0).encode())
    # Wait for the movement to complete
    while True:
        ser.write(b"?")
        response = ser.readline().strip().decode("utf-8")
        if "Idle" in response:
            break
    # Close serial port
    ser.close()

    # Write G-code to file
    with open('gcode.gcode', "w") as f:
        f.write("\n".join(gcode))

####################################################
####################################################
def main_start():
    start_time = time.time()
    print("1----------------------first------------------------")
    # Load the input image
    #put it 50 to minimize my work time to less number of lines
    img = resize_image(image_path,100)

    #cv2.imwrite('resized_image.png', img)
    # img=cv2.imread('home.png')
    contours = edited_image(img)
    # Get the height and width of the input image
    height, width, _ = img.shape
    # Create a copy of the image to draw the contours on
    img_contours = np.zeros_like(img)

    # Draw the contours on the image with thickness 1
    cv2.drawContours(img_contours, contours, -1, (0, 255, 0), 1)
    # Display the original and contour images using Matplotlib
    #plt.imshow(img_contours)
    #plt.show()

    # Create a new SVG drawing
    dwg = svgwrite.Drawing('../../out.svg', size=(width, height))
    # Convert the contours to SVG paths and add them to the drawing
    for contour in contours:
        path_data = ""
        for i in range(len(contour)):
            if i == 0:
                path_data += "M{},{} ".format(contour[i][0][0], contour[i][0][1])
            else:
                path_data += "L{},{} ".format(contour[i][0][0], contour[i][0][1])
        dwg.add(dwg.path(d=path_data, fill="none", stroke="black"))

    # Save the SVG drawing to a file
    dwg.save()
    print("2-------------------svg file done------------------------")
    # Convert SVG paths to line segments
    paths, attributes = svg2paths('../../out.svg')
    lines = svgtolines(paths, attributes)
    # Extract dimensions of SVG file
    svg_document = minidom.parse('../../out.svg')
    svg_tag = svg_document.getElementsByTagName('svg')[0]
    #scale factor of an original {image in cm} we can maximaize it or minimize it at default = 1 px in cm
    s_f = 1
    #convert px to cm for an any image we put it but before we minimize the scale by 2 but for vector mapping multiply it by 2
    width = float(svg_tag.getAttribute('width').replace('px', '')) * 0.02 * s_f # px to cm 1px = 0.02 mm scale factor
    height = float(svg_tag.getAttribute('height').replace('px', '')) * 0.02 * s_f# px to cm 1px = 0.02 mm scale factor
    # Find maximum values for x and y coordinates
    max_x = max([max([line.start.real, line.end.real]) for line in lines])
    max_y = max([max([line.start.imag, line.end.imag]) for line in lines])
    if not lines:
        max_x = 0
        max_y = 0


    print("3--------------svgtolines done-----------------")

    # Scale the G-code to fit within the dimensions of the SVG file
    distances = optimize_line(lines)
    print("4------------optimize_line done----------------")
    times2 = time.time()
    path = solve_tsp(distances)
    timee2 = time.time()
    totaltsptime = timee2 - times2
    print("Total Run Time = ", totaltsptime, " seconds")
    print("5----------------solve_tsp---------------------")
    optimized_lines = [lines[i] for i in path]
    # Scale the G-code to fit within the dimensions of the SVG file
    scale_factor = min(width / max_x, height / max_y)
    for i in range(len(optimized_lines)):
        start = optimized_lines[i].start * scale_factor
        end = optimized_lines[i].end * scale_factor
        optimized_lines[i] = svgpathtools.Line(start, end)

    print("1----------------------------------------------")
    # Convert the optimized lines to G-code
    gcode_generator(optimized_lines, laser_speed, laser_power,(width, height))

    end_time = time.time()
    total_time = end_time - start_time
    print("Total Run Time = ", total_time, " seconds")

    ####################################################
    ####################################################
import tkinter as tk
from tkinter import ttk
from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk
import serial.tools.list_ports
import tkinter.font as tkFont
from tkinter.scrolledtext import ScrolledText

def virtualize_button():
    clean_canvas_text()
    main_start()
# Create a function to close the window
def exit_program():
    root.destroy()

def exit_window2():
    send_gcode_command('G90X0Y0F500')
    window2.destroy()


def exit_window3():
    window3.destroy()

def clean_canvas_text():
    canvas.delete("all")

def send_gcode_command(gcode):
    ser = serial.Serial('COM8', 115200, timeout=1)
    ser.write(gcode.encode('utf-8'))
    # Wait for the movement to complete
    while True:
        ser.write(b"?")
        response = ser.readline().strip().decode("utf-8")
        if "Idle" in response:
            break
    print("-------test----------\n",gcode)
    #ser.close()

import tkinter as tk

def button_click():
    print("Virtualize button clicked")

def Clean_canvas():
    clean_canvas_text()


import tkinter as tk

# Global variable to store image path
image_path = None

# Set laser power and speed
laser_power = 100  # in watts
laser_speed = 1500  # in mm/s

# Function for button1
def open_image():
    canvas.delete("all")
    global image_path
    # Open a file dialog to select an image
    file_path = filedialog.askopenfilename()
    # Check if a file was selected
    if file_path:
        # Save the image path to the global variable
        image_path = file_path
        # Open and display the image
        img = Image.open(image_path)
        img = img.resize((canvas_width, canvas_height))
        photo = ImageTk.PhotoImage(img)
        canvas.create_image(canvas_width / 2, canvas_height / 2, image=photo)
        canvas.image = photo  # keep a reference to the image to prevent garbage collection

"""
directional fuctions
"""
ser = None

def establish_connection():
    global ser
    ser = serial.Serial('COM8', 115200) # Replace COM3 with the serial port connected to the GRBL board

def right():
    ser.write(b'G91 X1\n') # Move X-axis positively by 1 unit in relative mode
def left():
    ser.write(b'G91 X-1\n') # Move X-axis positively by 1 unit in relative mode
def up():
    ser.write(b'G91 Y1\n') # Move X-axis positively by 1 unit in relative mode
def down():
    ser.write(b'G91 Y-1\n') # Move X-axis positively by 1 unit in relative mode
def up_right():
    ser.write(b'G91 X1 Y1\n') # Move X-axis positively by 1 unit in relative mode
def up_left():
    ser.write(b'G91 X-1 Y1\n') # Move X-axis positively by 1 unit in relative mode
def down_left():
    ser.write(b'G91 X-1 Y-1\n')  # Move X-axis positively by 1 unit in relative mode
def down_right():
    ser.write(b'G91 X1 Y-1\n')  # Move X-axis positively by 1 unit in relative mode
def go_to_origin():
    # Wait for the machine to be idle
    ser.write(b'?\n')
    response = ser.readline().strip()
    while response != b'ok':
        response = ser.readline().strip()
    # Set absolute coordinates
    ser.write(b'G90\n')
    # Move to (0,0)
    ser.write(b'G0 X0 Y0\n')
    window2.destroy()
def laser_power_1():
    ser.write(b'M3 S50\n')  # Set laser power to 50
    time.sleep(2)  # Delay for 2 seconds
    ser.write(b'M5\n')  # Turn off the laser

def laser_power_2():
    ser.write(b'M3 S250\n')  # Set laser power to 250
    time.sleep(2)  # Delay for 2 seconds
    ser.write(b'M5\n')  # Turn off the laser

def laser_power_3():
    ser.write(b'M3 S1000\n')  # Set laser power to 1000
    time.sleep(2)  # Delay for 2 seconds
    ser.write(b'M5\n')  # Turn off the laser


#------------------------------------------
#----------direction button----------------
def direction_button():
    global screen_width, screen_height

    # Calculate size and position of new window
    window_width = int(screen_width)
    window_height = int(screen_height)
    window_x = int(screen_width / 2)
    window_y = int(screen_height/ 2)
    global window2
    # Create new window
    window2 = tk.Toplevel(root)
    window2.geometry("{}x{}+{}+{}".format(window_width, window_height, window_x, window_y))
    window2.attributes('-fullscreen', True)
    window2.configure(bg='#111111')  # Change background color to dark
    # Add widgets to the new window (e.g. labels, buttons, etc.)
    # ...
    global homePhoto
    global upArrow
    global downArrow
    global topLeftArrow
    global topRightArrow
    global leftArrow
    global rightArrow
    global downRightArrow
    global downLeftArrow
    img_1 = Image.open('icons/home.png')
    img_1 = img_1.resize((100, 100))  # resize image to fit button
    homePhoto = ImageTk.PhotoImage(img_1)

    img_2 = Image.open('icons/up.png')
    img_2 = img_2.resize((110, 110))  # resize image to fit button
    upArrow = ImageTk.PhotoImage(img_2)

    img_3 = Image.open('icons/Down.png')
    img_3 = img_3.resize((100, 100))  # resize image to fit button
    downArrow = ImageTk.PhotoImage(img_3)

    img_4 = Image.open('icons/left.png')
    img_4 = img_4.resize((100, 100))  # resize image to fit button
    leftArrow = ImageTk.PhotoImage(img_4)


    img_5 = Image.open('icons/right.png')
    img_5 = img_5.resize((100, 100))  # resize image to fit button
    rightArrow = ImageTk.PhotoImage(img_5)

    img_6 = Image.open('icons/topLeft.png')
    img_6 = img_6.resize((100, 100))  # resize image to fit button
    topLeftArrow = ImageTk.PhotoImage(img_6)

    img_7 = Image.open('icons/topRight.png')
    img_7 = img_7.resize((100, 100))  # resize image to fit button
    topRightArrow = ImageTk.PhotoImage(img_7)

    img_8 = Image.open('icons/downLeft.png')
    img_8 = img_8.resize((100, 100))  # resize image to fit button
    downLeftArrow= ImageTk.PhotoImage(img_8)

    img_9 = Image.open('icons/downRight.png')
    img_9 = img_9.resize((100, 100))  # resize image to fit button
    downRightArrow = ImageTk.PhotoImage(img_9)


    GLabel_8582 = tk.Label(window2, fg='#ffffff',bg='#111111', justify='left', text="Machine Movement")
    ft = tkFont.Font(family='arial', size=17, weight='bold')
    GLabel_8582["font"] = ft
    GLabel_8582.grid(row=0, column=2, padx=1, pady=1, sticky='nsew')

    homeButton = tk.Button(window2, image=homePhoto, command=go_to_origin, font=('Arial', 10),bg='#1C658C', fg='#FFFFFF', width=100, height=100, bd=2, highlightthickness=2,highlightbackground='#566665', highlightcolor='#566665')
    topButton = tk.Button(window2, image=upArrow, command=up, font=('Arial', 10), bg='#1C658C',fg='#FFFFFF', width=100, height=100, bd=2, highlightthickness=2,highlightbackground='#566665', highlightcolor='#566665')
    topLeftButton = tk.Button(window2, image=topLeftArrow,command=up_left, font=('Arial', 10), bg='#1C658C',fg='#FFFFFF', width=100, height=100, bd=2, highlightthickness=2,highlightbackground='#566665', highlightcolor='#566665')
    leftButton = tk.Button(window2, image=leftArrow,command=left , font=('Arial', 10), bg='#1C658C',fg='#FFFFFF', width=100, height=100, bd=2, highlightthickness=2,highlightbackground='#566665', highlightcolor='#566665')
    topRightButton = tk.Button(window2, image=topRightArrow,command=up_right ,font=('Arial', 10), bg='#1C658C',fg='#FFFFFF', width=100, height=100, bd=2, highlightthickness=2,highlightbackground='#566665', highlightcolor='#566665')
    rightButton = tk.Button(window2, image=rightArrow,command=right ,font=('Arial', 10), bg='#1C658C', fg='#FFFFFF', width=100, height=100, bd=2, highlightthickness=2,highlightbackground='#566665', highlightcolor='#566665')
    downButton = tk.Button(window2, image=downArrow,command=down ,font=('Arial', 10), bg='#1C658C',fg='#FFFFFF', width=100, height=100, bd=2, highlightthickness=2,highlightbackground='#566665', highlightcolor='#566665')
    downLeftButton = tk.Button(window2, image=downLeftArrow,command=down_left ,font=('Arial', 10), bg='#1C658C',fg='#FFFFFF', width=120, height=120, bd=2, highlightthickness=2,highlightbackground='#566665', highlightcolor='#566665')
    downRightButton = tk.Button(window2, image=downRightArrow,command= down_right,font=('Arial', 10), bg='#1C658C',fg='#FFFFFF', width=120, height=120, bd=2, highlightthickness=2,highlightbackground='#566665', highlightcolor='#566665')

    homeButton.grid(row=2, column=2, padx=10, pady=10,sticky='nsew')
    topButton.grid(row=1, column=2, padx=10, pady=10,sticky='nsew')
    topLeftButton.grid(row=1, column=1, padx=10, pady=10,sticky='nsew')
    topRightButton.grid(row=1, column=3, padx=10, pady=10,sticky='nsew')
    leftButton.grid(row=2, column=1, padx=10, pady=10,sticky='nsew')
    rightButton.grid(row=2, column=3, padx=10, pady=10,sticky='nsew')
    downButton.grid(row=3, column=2, padx=10, pady=10,sticky='nsew')
    downLeftButton.grid(row=3, column=1, padx=10, pady=10,sticky='nsew')
    downRightButton.grid(row=3, column=3, padx=10, pady=10,sticky='nsew')

    window2.grid_columnconfigure(0, weight=1)
    window2.grid_columnconfigure(1, weight=1)
    window2.grid_rowconfigure(0, weight=1)
    window2.grid_rowconfigure(1, weight=1)
    window2.grid_columnconfigure(2, weight=1)
    window2.grid_rowconfigure(2, weight=1)
    window2.grid_columnconfigure(3, weight=1)
    window2.grid_rowconfigure(3, weight=1)
    window2.grid_columnconfigure(4, weight=1)
    window2.grid_rowconfigure(4, weight=1)

    # Make the new window visible
    window2.deiconify()



def Laser_power():
    global screen_width, screen_height

    # Calculate size and position of new window
    window_width = int(screen_width)
    window_height = int(screen_height)
    window_x = int(screen_width / 2)
    window_y = int(screen_height/ 2)

    global red
    global yellow
    global green
    global returnHome
    global window3

    img_1 = Image.open('icons/redButton3.png')
    img_1 = img_1.resize((140, 140))  # resize image to fit button
    red = ImageTk.PhotoImage(img_1)

    img_2 = Image.open('icons/yellowButton.png')
    img_2 = img_2.resize((170, 170))  # resize image to fit button
    yellow = ImageTk.PhotoImage(img_2)

    img_3 = Image.open('icons/greenButton.png')
    img_3 = img_3.resize((160, 160))  # resize image to fit button
    green = ImageTk.PhotoImage(img_3)

    img_4 = Image.open('icons/left.png')
    img_4 = img_4.resize((60, 60))  # resize image to fit button
    returnHome = ImageTk.PhotoImage(img_4)

    # Create new window
    window3 = tk.Toplevel(root)
    window3.geometry("{}x{}+{}+{}".format(window_width, window_height, window_x, window_y))
    window3.attributes('-fullscreen', True)
    window3.configure(bg='#111111')  # Change background color to dark
    returnbButton = tk.Button(window3, image=returnHome, command=exit_window3, font=('Arial', 10), bg='#111111', fg='#FFFFFF',
                          width=60, border=0, height=60, highlightthickness=2, )

    GLabel = tk.Label(window3, fg='#ffffff', bg='#111111', justify='left', text="Test Laser Power")
    ft = tkFont.Font(family='arial', size=22, weight='bold')
    GLabel["font"] = ft
    GLabel.grid(row=0, column=2, padx=1, pady=1, sticky='nsew')
    redButton = tk.Button(window3, image=red, command=laser_power_3, font=('Arial', 10), bg='#111111', fg='#FFFFFF', width=140,border=0, height=140, highlightthickness=2, )
    yellowButton = tk.Button(window3, image=yellow, command=laser_power_2, font=('Arial', 10), bg='#111111', fg='#FFFFFF',width=170, border=0, height=170, highlightthickness=2, )
    greenButton = tk.Button(window3, image=green, command=laser_power_1, font=('Arial', 10), bg='#111111', fg='#FFFFFF',width=160, border=0, height=160, highlightthickness=2, )

    redButton.grid(column=1,row=2)
    yellowButton.grid(column=2, row=2)
    greenButton.grid(column=3, row=2)

    redLabel = tk.Label(window3, fg='#ffffff', bg='#111111', justify='left', text="Strong Laser")
    ft = tkFont.Font(family='arial', size=20, weight='bold')
    redLabel["font"] = ft

    yellowLabel = tk.Label(window3, fg='#ffffff', bg='#111111', justify='left', text="Medium Laser")
    ft = tkFont.Font(family='arial', size=20, weight='bold')
    yellowLabel["font"] = ft

    greenLabel = tk.Label(window3, fg='#ffffff', bg='#111111', justify='left', text="Weak Laser")
    ft = tkFont.Font(family='arial', size=20, weight='bold')
    greenLabel["font"] = ft

    returnbButton.grid(row=0, column=0, padx=1, pady=1, sticky='nsew')
    greenLabel.grid(row=3, column=3, padx=1, pady=1, sticky='nsew')
    yellowLabel.grid(row=3, column=2, padx=1, pady=1, sticky='nsew')
    redLabel.grid(row=3, column=1, padx=1, pady=1, sticky='nsew')
    window3.grid_columnconfigure(0, weight=1)
    window3.grid_columnconfigure(1, weight=1)
    window3.grid_rowconfigure(0, weight=1)
    window3.grid_rowconfigure(1, weight=1)
    window3.grid_columnconfigure(2, weight=1)
    window3.grid_rowconfigure(2, weight=1)
    window3.grid_columnconfigure(3, weight=1)
    window3.grid_rowconfigure(3, weight=1)
    window3.grid_columnconfigure(4, weight=1)
    window3.grid_rowconfigure(4, weight=1)

    window3.deiconify()
#--------------------------------
#--------------------------------
# Create a window and set its properties
def close_connection():
    ser.close()

establish_connection()

root = tk.Tk()
root.title('My GUI')
root.geometry('800x480')
# Get screen dimensions
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
# Hide the title bar
#root.overrideredirect(True)
# Maximize the window to fill the screen
root.attributes('-fullscreen', True)
root.configure(bg='#111111')  # Change background color to dark
img = Image.open('icons/1.png')
img = img.resize((85, 85)) # resize image to fit button
photo = ImageTk.PhotoImage(img)

img2 = Image.open('icons/2.png')
img2 = img2.resize((85, 85)) # resize image to fit button
photo2 = ImageTk.PhotoImage(img2)
img3 = Image.open('icons/direction2.png')
img3 = img3.resize((120, 120)) # resize image to fit button
photo3 = ImageTk.PhotoImage(img3)
img4 = Image.open('icons/4.png')
img4 = img4.resize((85, 85)) # resize image to fit button
photo4 = ImageTk.PhotoImage(img4)

button1 = tk.Button(root, image=photo, command=open_image, compound='bottom', font=('Arial', 10), bg='#EEEEEE', fg='#FFFFFF', width=100, height=100, bd=2, highlightthickness=2, highlightbackground='#566665', highlightcolor='#566665')
button2 = tk.Button(root, image=photo2,command = virtualize_button, compound='bottom', font=('Arial', 10), bg='#577D86', fg='#FFFFFF', width=100, height=100, bd=2, highlightthickness=2, highlightbackground='#566665', highlightcolor='#566665')
button3 = tk.Button(root, image=photo3, command=direction_button, compound='bottom', font=('Arial', 10), bg='#1C658C', fg='#FFFFFF', width=100, height=100, bd=2, highlightthickness=2, highlightbackground='#566665', highlightcolor='#566665')
button4 = tk.Button(root, image=photo4, command= Laser_power, compound='bottom', font=('Arial', 10), bg='#FFFAA4', fg='#FFFFFF', width=100, height=100, bd=2, highlightthickness=2, highlightbackground='#566665', highlightcolor='#566665')

# Place the buttons in a grid layout
button1.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
button2.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')
button3.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
button4.grid(row=1, column=1, padx=10, pady=10, sticky='nsew')

# Create a canvas to fill the remaining space
canvas = tk.Canvas(root, bg='#333333', bd=2, highlightthickness=2,highlightbackground='#566665', highlightcolor='#111111')

canvas.grid(row=0, column=2, rowspan=3, padx=10, pady=10, sticky='nsew')

# Calculate canvas size based on screen size
canvas_width = int(root.winfo_screenwidth() * 0.6)
canvas_height = int(root.winfo_screenheight())
#------------------------------
img5 = Image.open('icons/reset.png')
img5 = img5.resize((110, 110)) # resize image to fit button
photo5 = ImageTk.PhotoImage(img5)

img6 = Image.open('icons/1.png')
img6 = img6.resize((85, 85)) # resize image to fit button
photo6 = ImageTk.PhotoImage(img6)
global photo7
img7 = Image.open('icons/2.png')
img7 = img7.resize((85, 85)) # resize image to fit button
photo7 = ImageTk.PhotoImage(img7)

img8 = Image.open('icons/exist.png')
img8 = img8.resize((85, 85)) # resize image to fit button
photo8 = ImageTk.PhotoImage(img8)

button5 = tk.Button(root, image=photo5, command=clean_canvas_text, compound='bottom', font=('Arial', 10), bg='#525252', fg='#FFFFFF', width=100, height=100, bd=2, highlightthickness=2, highlightbackground='#566665', highlightcolor='#566665')
button6 = tk.Button(root, image=photo8, command=exit_program, compound='bottom', font=('Arial', 10), bg='#541212', fg='#FFFFFF', width=100, height=100, bd=2, highlightthickness=2, highlightbackground='#566665', highlightcolor='#566665')
#----------------------
#----run button--------


#----------------------
#----------------------
button5.grid(row=2, column=0, padx=10, pady=10, sticky='nsew')
button6.grid(row=2, column=1, padx=10, pady=10, sticky='nsew')



#------------------------------


# Resize the buttons and canvas to fit the screen
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=3)
root.grid_rowconfigure(2, weight=1)

root.protocol("WM_DELETE_WINDOW", close_connection) # Close the serial connection when the window is closed
# Run the main loop
root.mainloop()
