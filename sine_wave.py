import math
import machine
import ssd1306

i2c = machine.I2C(sda=machine.Pin(4), scl=machine.Pin(5))

display = ssd1306.SSD1306_I2C(128, 32, i2c)

def draw_sine(display, period=2, amplitude=16, y_offset=0, x_offset=0):
    display.fill(0)
    display.show()
    for i in range(128):
        wave = int(math.sin((i + x_offset) / (period * math.pi)) * amplitude + (y_offset + 16))
        if ( 0 > wave ):
            wave = 0
        display.pixel(i, wave, 0xFF)
    display.show()
