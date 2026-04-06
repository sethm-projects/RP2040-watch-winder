from machine import Pin, I2C
import time
import ssd1306

#spi = machine.SPI(0, )

led = Pin("LED", Pin.OUT)

# while True:
#     led.off()
#     time.sleep(2)
#     led.on()
#     time.sleep(2)

# ssd1306 0.91 inch 128*32 display, white, i2c
width = 128
height = 32
VccDisp = Pin(2,Pin.OUT, value = 1)
i2c = I2C(0,sda = Pin(0),scl = Pin(1),freq = 400000)
display = ssd1306.SSD1306_I2C(width, height, i2c)

# Hello world
display.text('Hello, World!', 0, 0, 1)
display.show()

time.sleep(2)

display.poweroff()