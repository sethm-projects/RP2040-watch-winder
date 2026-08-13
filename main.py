import uasyncio as asyncio
from machine import Pin, I2C, RTC
import time
import ssd1306

from switch import Switch

# ssd1306 0.91 inch 128*32 display, white, i2c
width = 128
height = 32
VccDisp = Pin(2,Pin.OUT, value = 1)
i2c = I2C(0,sda = Pin(0),scl = Pin(1),freq = 400000)
display = ssd1306.SSD1306_I2C(width, height, i2c)

# KY-040 rotary encoder on voltage supply/resistor board
VccEnc = Pin(12, Pin.OUT, value = 1)
sw_pin = Pin(13,Pin.IN, Pin.PULL_UP)
a = Pin(14,Pin.IN,Pin.PULL_UP)
b = Pin(15,Pin.IN,Pin.PULL_UP)

sw = Switch(sw_pin, 50)

# Hello world
display.text('Hello, World!', 0, 0, 1)
display.show()

#First connection test for DS3231 RTC
devices = i2c.scan()
if len(devices) == 0:
    print("no i2c device")
else:
    print('i2c devices found:')
    for device in devices:
        print(hex(device))
        
# try:
#     rtc = RTC()
# except:
#     print("rtc type not supported by machine")
#     rtc = None

# #Listen for switch state change
async def watch_switch():
    # #initialize toggle for switch on rotary encoder
    switch_toggle = 0
    switch_state_last = 1
    switch_state_current = sw.state()

    while True:
        await sw.wait_for_state_change()
        switch_state_current = sw.state()
        if switch_state_last != switch_state_current:
            switch_state_last = switch_state_current # re-set last state for next iteration
            if switch_state_current == 0:
                if switch_toggle == 0:
                    display.poweroff()
                    switch_toggle = 1
                elif switch_toggle == 1:
                    display.poweron()
                    switch_toggle = 0

asyncio.create_task(watch_switch())
