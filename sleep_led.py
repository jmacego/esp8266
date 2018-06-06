"""sleep_led.py

Mimics the apple sleep LEDs that probably don't exist anymore. Comforting
sin-wave effect.
"""

import machine
import uasyncio as asyncio
import time
import math


pwm = machine.PWM(machine.Pin(2))

pwm.freq(1000)


loop = asyncio.get_event_loop()

async def sleep_led(l, t):
    while True:
        for i in range(100):
            wave = int(math.sin(i / (10 * math.pi)) * 1024)
            if ( 0 > wave ):
                wave = 0
            l.duty(wave)
            await asyncio.sleep_ms(t)


async def print_hello(delay_secs):
    total_time = 0
    while True:
        await asyncio.sleep(delay_secs)
        total_time += delay_secs
        print("Hello, World, it's been: " + str(total_time) + " seconds")


loop.create_task(sleep_led(pwm, 31))
loop.create_task(print_hello(5))

loop.run_forever()

