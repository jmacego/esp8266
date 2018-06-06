import math
import machine
import ssd1306
import framebuf
import utime as time


def draw_sine(display, period=2, amplitude=16, y_offset=0, x_offset=0):
    display.fill(0)
    display.show()
    for i in range(128):
        wave = int(math.sin((i + x_offset) / (period * math.pi)) * amplitude +
                   (y_offset + 16))

        if (0 > wave):
            wave = 0
        display.pixel(i, wave, 0xFF)
    display.show()


def draw_micropython(display):
    buffer = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xe0\x10\x8a\xa0\x10\x24\xc8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x78\xfe\xff\x3f\xfe\xfd|\xfb\xf8\xfc\xff\x7c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\xc0\x64\xe0\xe0\xe0\xc0\xc1\x63\x9f\xff\x0f\xce\xff\xff\xcf\xe3\xf0pp\xa0\xe0\xe0\xc0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf0\xff\xfb\xe7\xdf\x8e\x9e\xfd\x95"$%\x00\xfe\xff\xff\xed\xdd\xce\xce\xff\xe7\xe7\xf7\xfb\xf9\xfep\xe0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00@6\x9bg7\xcfo\x9d\xdb?\xbbws\xf7\xfa\xfa\xf9\xf4\xfd\xf7\xf3\xf1\xfdsy\xbd;\xd9\x9do\xcc6g\x9b6@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x02\x01\x04\x03\t\x06\x13\x0c&\x19\r\x1b\x1b\r\x19&\x0c\x13\x06\t\x03\x04\x01\x02\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
    fb = framebuf.FrameBuffer(buffer, 48, 48, framebuf.MVLSB)
    display.fill(0)
    display.blit(fb, 8, 0)
    display.text("Micro", 60, 0)
    display.text("Python", 70, 10)
    display.show()


class Paddle:
    """Paddle Class

    Creates and modifies the Pong Paddles"""

    def __init__(self, display, x, h):
        self.display = display
        self.y = self.display.height // 2 - h // 2
        self.h = h
        self.x = x
        self.c = 1

    def move(self, y):
        self.x += y

    def show(self):
        self.display.vline(self.x, self.y, self.h, self.c)


class Ball:
    """Ball Class

    Creates and modifies the Pong Ball"""
    def __init__(self, display, paddle1, paddle2, x=64, y=16,
                 vector={"x": -1, "y": 1}):
        self.display = display
        self.x = x
        self.y = y
        self.vector = vector
        self.paddle1 = paddle1
        self.paddle2 = paddle2

    def update(self):
        self.x += self.vector['x']
        if self.x >= display.width:
            self.display.text("Game Over", 30, 12)
            return True
        elif self.x <= 0:
            self.display.text("Game Over", 30, 12)
            return True

        self.y += self.vector['y']
        if self.y >= self.display.height:
            self.y = self.display.height
            self.vector['y'] *= -1
        elif self.y <= 0:
            self.y = 0
            self.vector['y'] *= -1

        if self.x == self.paddle1.x:
            if self.paddle1.y <= self.y <= self.paddle1.y + self.paddle1.h:
                self.vector['x'] *= -1
        if self.x == self.paddle2.x:
            if self.paddle1.y <= self.y <= self.paddle2.y + self.paddle2.h:
                self.vector['x'] *= -1

        self.display.pixel(self.x, self.y, 1)

        return False

    def move_paddle(self, paddle):
        if paddle.x - paddle.h < self.x < paddle.x + paddle.h:
            half_height = paddle.h // 2
            if paddle.y < self.y - half_height:
                paddle.y += 1
            elif paddle.y > self.y - half_height:
                paddle.y -= 1
            print("Paddle.y Set: {}".format(paddle.y))
            bottom = paddle.y - paddle.h
            if paddle.y <= 0:
                paddle.y = 0
                print("Paddle.y hit top: {}".format(paddle.y))
            elif paddle.y >= self.display.height - paddle.h:
                paddle.y = self.display.height - paddle.h
                print("Paddle.y hit bottom: {}".format(paddle.y))


i2c = machine.I2C(sda=machine.Pin(4), scl=machine.Pin(5))

display = ssd1306.SSD1306_I2C(128, 32, i2c)

draw_micropython(display)
time.sleep(5)

paddle1 = Paddle(display, 10, 10)
paddle2 = Paddle(display, 118, 10)
ball = Ball(display, paddle1, paddle2)

game_over = False
for i in range(5000):
    display.fill(0)
    paddle1.show()
    paddle2.show()
    game_over = ball.update()
    ball.move_paddle(paddle1)
    ball.move_paddle(paddle2)
    display.show()
    time.sleep_ms(10)
    if game_over:
        print("Game Over")
        break
