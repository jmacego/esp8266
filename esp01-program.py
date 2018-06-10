#!/usr/bin/env python3
"""ESP01 Programmer for Raspberry Pi

Unlike dev boards with CP210x chips esptool has no way to reset the
board or set the program pin low. Pin values below have no meaning,
they were just convenient to me.

RST_PIN = BCM16, BOARD36
PRG_PIN = BCM21, BOARD38

This is a quick hack, leaving it in run will not clean up GPIO, there
is an early start for catching control-c, which I generally do on RPi
stuff in which case you could just leave run as an infinite loop and
call GPIO.cleanup() and sys.exit from within the callback handler but
I didn't feel like finishing it as it's Good Enough for Me.
"""
import sys
import RPi.GPIO as GPIO
import time
import signal
from subprocess import Popen, PIPE


def start_programming(rst_pin=16, prg_pin=21):
    """Set program and the reset"""
    GPIO.output(prg_pin, GPIO.LOW)
    reset(rst_pin, prg_pin)

def reset(rst_pin=16, prg_pin=21):
    """Reset the ESP01"""
    GPIO.output(rst_pin, GPIO.LOW)
    time.sleep(0.1)
    GPIO.output(rst_pin, GPIO.HIGH)

def stop_programming(rst_pin=16, prg_pin=21):
    """Unset program and then reset"""
    GPIO.output(prg_pin, GPIO.HIGH)
    reset(rst_pin, prg_pin)

def run(command):
    """Run a command and give realtime(ish) output"""
    process = Popen(command, stdout=PIPE, shell=True)
    while True:
        line = process.stdout.readline().rstrip()
        if not line:
            break
        yield line

def sigint_handler(signum, frame):
    pass

signal.signal(signal.SIGINT, sigint_handler)


if __name__ == "__main__":
    rst_pin = 16
    prg_pin = 21

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup((rst_pin, prg_pin), GPIO.OUT)

    if sys.argv[1] == "esptool.py":
        start_programming(rst_pin, prg_pin)

        for line in run(" ".join(sys.argv[1:])):
            print(line.decode("utf-8"))

        stop_programming(rst_pin, prg_pin)
    elif sys.argv[1] == "ampy":
        reset()
        for line in run(" ".join(sys.argv[1:])):
            print(line.decode("utf-8"))
    elif sys.argv[1] == "run":
        reset()
        sys.exit()
    else:
        reset()
    GPIO.cleanup()
