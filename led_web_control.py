"""Simple web app for micropython on the esp8266 that allows control
of the LED, including a sin-based sleep mode.

Uses Picoweb and the uasyncio library with the additional asyn.py
which have to all be loaded using upip into the sdk and frozen
as bytecode - I'll make instructions on this some day as that ate
up 2/3 or more of my development time.

Expects a config.json file in the format:
{"ssid": "SSIDGOESHERE", "password": "PASSWORDGOESHERE"}

This file can be simply generated on the device by:

import json
config = {"ssid": "SSIDGOESHERE", "password": "PASSWORDGOESHERE"}
with open('config.json', 'w') as outfile:
    json.dump(config, outfile)


"""
import picoweb
import network
import micropython
import gc
import logging
import ntptime
import machine
import uasyncio as asyncio
import time
import math
import ure as re
import utime as time
import uasyncio.asyn as asyn
import json

LED_PIN = const(2)
PWM_FREQ = const(1000)
LED_INVERT = True


@asyn.cancellable
async def do_sleep_led(pin, t):
    led = machine.PWM(machine.Pin(pin))
    led.freq(PWM_FREQ)
    while True:
        for i in range(100):
            wave = int(math.sin(i / (10 * math.pi)) * 1024)
            if (0 > wave):
                wave = 0
            led.duty(wave)
            await asyncio.sleep_ms(t)


@asyn.cancellable
async def print_hello(delay_secs):
    total_time = 0
    while True:
        await asyncio.sleep(delay_secs)
        total_time += delay_secs
        print("Hello, World, it's been: " + str(total_time) + " seconds")


async def periodic_gc():
    while True:
        await asyncio.sleep(1)
        gc.collect()
        gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())


def do_connect():
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        with open('config.json') as f:
            config = json.load(f)

        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(config['ssid'], config['password'])
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())

    try:
        ntptime.settime()
    except(OSError):
        print("Caught an NTP timeout =(")

    year, month, day, hour, minute, second, weekday, yearday = time.localtime()
    machine.RTC().datetime((year, month, day, weekday, hour, minute, second, 0))
    return sta_if.ifconfig()[0]


app = picoweb.WebApp(__name__)


@app.route("/")
def index(req, resp):
    yield from picoweb.start_response(resp)
    yield from resp.awrite("<pre>There are {} bytes of free memory</pre>".format(str(gc.mem_free())))
    yield from resp.awrite("<br><a href='/gc'>Run Garbage Collection</a>")
    yield from resp.awrite("<br><a href='/time_page'>Time Stuff</a>")
    yield from resp.awrite("<br><a href='/sleep_led'>Start the Sleep LED sequence</a>")
    yield from resp.awrite("<br><a href='/stop_led'>Stop the Sleep LED sequence</a>")
    yield from resp.awrite("<br><a href='/led_on'>Turn the LED on</a>")
    yield from resp.awrite("<br><a href='/led_off'>Turn the LED off</a>")


@app.route("/gc")
def garbage_collection(req, resp):
    yield from picoweb.start_response(resp)
    yield from resp.awrite("<pre>-----------------------------\n")
    yield from resp.awrite("Initial free: {} allocated: {}\n".format(gc.mem_free(), gc.mem_alloc()))
    gc.collect()
    yield from resp.awrite("After manual gc free: {} allocated: {}\n".format(
            gc.mem_free(), gc.mem_alloc()))
    yield from resp.awrite("<br><a href='/'>Back to Menu</a>")


# This is broken, issue with time.localtime() when called inside an async function
@app.route("/time_page")
def time_page(req, resp):
    months_of_year = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
    days_of_week = ['Monday', 'Tuesday', 'Wednesday',
                    'Thursday', 'Friday', 'Saturday', 'Sunday']

    year, month, day, hour, minute, second, weekday, yearday = time.localtime()

    rtc_year, rtc_month, rtc_day, rtc_weekday, rtc_hour, rtc_minute, rtc_second, \
            rtc_subsecond = rtc.datetime()

    rtc.datetime((year, month, day, weekday, hour, minute, second, 0))
    yield from picoweb.start_response(resp)
    yield from resp.awrite("It's {}, {} {}, {} - {}:{}:{} UTC".format(
            days_of_week[weekday], months_of_year[month], day, year, hour, minute, second))
    yield from resp.awrite("<br><a href='/'>Back to Menu</a>")


@app.route("/sleep_led")
def sleep_led(req, resp):
    yield from picoweb.start_response(resp)
    yield from resp.awrite("Starting the sleep LED sine goodness")

    loop = asyncio.get_event_loop()
    loop.create_task(asyn.Cancellable(do_sleep_led, LED_PIN, 31)())
    yield from resp.awrite("<br><a href='/stop_led'>Stop it</a>")
    yield from resp.awrite("<br><a href='/'>Back to Menu</a>")


@app.route("/stop_led")
def stop_led(req, resp):
    yield from picoweb.start_response(resp)
    yield from resp.awrite("Stopping the LED")
    await asyn.Cancellable.cancel_all()
    yield from resp.awrite("<br>Canceled running tasks")
    yield from resp.awrite("<br><a href='/sleep_led'>Start it again</a>")
    yield from resp.awrite("<br><a href='/'>Back to Menu</a>")


@app.route("/led_on")
def stop_led(req, resp):
    yield from picoweb.start_response(resp)
    machine.PWM(machine.Pin(LED_PIN)).deinit()
    if LED_INVERT == True:
        machine.Signal(machine.Pin(LED_PIN, machine.Pin.OUT),
                       invert=True).on()
    else:
        machine.Pin(LED_PIN, machine.Pin.OUT).on()
    yield from resp.awrite("<br>Turned the LED on")
    yield from resp.awrite("<br><a href='/led_off'>Turn it back off</a>")
    yield from resp.awrite("<br><a href='/'>Back to Menu</a>")

@app.route("/led_off")
def stop_led(req, resp):
    yield from picoweb.start_response(resp)
    machine.PWM(machine.Pin(LED_PIN)).deinit()
    if LED_INVERT == True:
        machine.Signal(machine.Pin(LED_PIN, machine.Pin.OUT),
                       invert=True).off()
    else:
        machine.Pin(LED_PIN, machine.Pin.OUT).off()
    yield from resp.awrite("<br>Turned the LED off")
    yield from resp.awrite("<br><a href='/led_on'>Turn it back on</a>")
    yield from resp.awrite("<br><a href='/'>Back to Menu</a>")


loop = asyncio.get_event_loop()

do_connect()


logging.basicConfig(level=logging.INFO)


#loop.create_task(sleep_led(LED_PIN, 31))
loop.create_task(asyn.Cancellable(print_hello, 5)())
# loop.create_task(print_hello(5))
loop.create_task(periodic_gc())

app.run(debug=True, host="0.0.0.0")
