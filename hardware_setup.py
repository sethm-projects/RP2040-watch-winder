# ssd1306_setup.py

from machine import Pin, I2C
import gc
import time
from drivers.ssd1306.ssd1306 import SSD1306 as SSD
from gui.core.ugui import Display

# ssd1306 0.91 inch 128*32 display, white, i2c
width = 128
height = 32
VccDisp = Pin(2,Pin.OUT, value = 1)
i2c = I2C(0,sda = Pin(0),scl = Pin(1),freq = 400000)

# KY-040 rotary encoder on voltage supply/resistor board
VccEnc = Pin(12, Pin.OUT, value = 1)
sw = Pin(13,Pin.IN, Pin.PULL_UP)
a = Pin(14,Pin.IN,Pin.PULL_UP)
b = Pin(15,Pin.IN,Pin.PULL_UP)

gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(i2c, width, height)  # Create a display instance

# Create and export a Display instance
# Define control buttons for encoder only mode
nxt = a  # Move to next control
sel = sw  # Operate current control
prev = b  # Move to previous control
increase = False  # Increase control's value
decrease = None  # Decrease control's value
display = Display(ssd, nxt, sel, prev, increase, decrease)