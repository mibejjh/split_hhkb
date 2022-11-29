import os
from time import sleep
import board
from digitalio import DigitalInOut, Direction, Pull
import usb_hid
import busio
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.mouse import Mouse
import supervisor

EXCLUDED_KEYS = {
    None,
    Keycode.F24,
    "Mouse Up",
    "Mouse Left",
    "Mouse Down",
    "Mouse Right",
    "Mouse Wheel Up",
    "Mouse Wheel Down",
    "Mouse Right Click",
    "Mouse Left Click",
    "Mouse Middle Click",
}

KEY_MAP = [
    [
        Keycode.ESCAPE,
        Keycode.ONE,
        Keycode.TWO,
        Keycode.THREE,
        Keycode.FOUR,
        Keycode.FIVE,
        Keycode.SIX,
        None,
        Keycode.SEVEN,
        Keycode.EIGHT,
        Keycode.NINE,
        Keycode.ZERO,
        Keycode.MINUS,
        Keycode.EQUALS,
        Keycode.BACKSLASH,
        Keycode.GRAVE_ACCENT,
    ],
    [
        Keycode.TAB,
        Keycode.Q,
        Keycode.W,
        Keycode.E,
        Keycode.R,
        Keycode.T,
        None,
        None,
        Keycode.Y,
        Keycode.U,
        Keycode.I,
        Keycode.O,
        Keycode.P,
        Keycode.LEFT_BRACKET,
        Keycode.RIGHT_BRACKET,
        Keycode.BACKSPACE,
    ],
    [
        Keycode.CONTROL,
        Keycode.A,
        Keycode.S,
        Keycode.D,
        Keycode.F,
        Keycode.G,
        None,
        None,
        Keycode.H,
        Keycode.J,
        Keycode.K,
        Keycode.L,
        Keycode.SEMICOLON,
        Keycode.QUOTE,
        None,
        Keycode.ENTER,
    ],
    [
        Keycode.LEFT_SHIFT,
        Keycode.Z,
        Keycode.X,
        Keycode.C,
        Keycode.V,
        Keycode.B,
        None,
        None,
        Keycode.B,
        Keycode.N,
        Keycode.M,
        Keycode.COMMA,
        Keycode.PERIOD,
        Keycode.FORWARD_SLASH,
        Keycode.RIGHT_SHIFT,
        Keycode.F24,
    ],
    [
        None,
        Keycode.WINDOWS,
        Keycode.LEFT_ALT,
        None,
        Keycode.SPACEBAR,
        None,
        None,
        None,
        Keycode.SPACEBAR,
        None,
        Keycode.RIGHT_ALT,
        Keycode.WINDOWS,
        None,
        None,
        None,
        None,
    ],
]
FN_KEY_MAP = [
    [
        Keycode.POUND,  # Keycode.ESCAPE,
        Keycode.F1,  #        Keycode.ONE,
        Keycode.F2,  #        Keycode.TWO,
        Keycode.F3,  #        Keycode.THREE,
        Keycode.F4,  #        Keycode.FOUR,
        Keycode.F5,  #        Keycode.FIVE,
        Keycode.F6,  #        Keycode.SIX,
        None,  #        None,
        Keycode.F7,  #        Keycode.SEVEN,
        Keycode.F8,  #        Keycode.EIGHT,
        Keycode.F9,  #        Keycode.NINE,
        Keycode.F10,  #        Keycode.ZERO,
        Keycode.F11,  #        Keycode.MINUS,
        Keycode.F12,  #        Keycode.EQUALS,
        Keycode.INSERT,  #        Keycode.BACKSLASH,
        Keycode.DELETE,  #        Keycode.GRAVE_ACCENT,
    ],
    [
        Keycode.CAPS_LOCK,  #         Keycode.TAB,
        Keycode.Q,
        "Mouse Wheel Up",
        "Mouse Up",
        "Mouse Wheel Down",
        Keycode.T,
        None,  #         None,
        None,  #         None,
        Keycode.Y,
        Keycode.U,
        Keycode.PRINT_SCREEN,  #         Keycode.I,
        Keycode.SCROLL_LOCK,  #         Keycode.O,
        Keycode.PAUSE,  #         Keycode.P,
        Keycode.UP_ARROW,  #         Keycode.LEFT_BRACKET,
        Keycode.RIGHT_BRACKET,
        Keycode.BACKSPACE,  #         Keycode.DELETE,
    ],
    [
        Keycode.CONTROL,
        Keycode.A,
        "Mouse Left",  # Keycode.S,
        "Mouse Down",  # Keycode.D,
        "Mouse Right",  # Keycode.F,
        Keycode.G,
        None,
        None,
        Keycode.H,
        Keycode.J,
        Keycode.HOME,  #         Keycode.K,
        Keycode.PAGE_UP,  #         Keycode.L,
        Keycode.LEFT_ARROW,  #         Keycode.SEMICOLON,
        Keycode.RIGHT_ARROW,  #         Keycode.QUOTE,
        None,  #         None,
        Keycode.ENTER,  #         Keycode.ENTER,
    ],
    [
        Keycode.LEFT_SHIFT,
        Keycode.Z,
        Keycode.X,
        Keycode.C,
        Keycode.V,
        Keycode.B,
        None,
        None,
        Keycode.B,
        Keycode.N,
        Keycode.M,
        Keycode.END,  #         Keycode.COMMA,
        Keycode.PAGE_DOWN,  #         Keycode.PERIOD,
        Keycode.DOWN_ARROW,  #         Keycode.FORWARD_SLASH
        Keycode.RIGHT_SHIFT,
        Keycode.F24,
    ],
    [
        None,
        Keycode.WINDOWS,
        Keycode.LEFT_ALT,
        None,
        "Mouse Right Click",
        None,
        None,
        None,
        "Mouse Left Click",
        None,
        Keycode.RIGHT_ALT,
        Keycode.WINDOWS,
        None,
        None,
        None,
        None,
    ],
]


class BaseMouse:
    def __init__(self) -> None:
        self.mouse = Mouse(usb_hid.devices)
        self.prev_mouse_state = set()
        self.dx = self.dy = self.dwheel = 0
        self.acc = 3.0

    def on_mouse_state(self, *states):
        current_states = set(states)

        if states:
            print(states)

        pressed = current_states - self.prev_mouse_state
        released = self.prev_mouse_state - current_states
        if pressed:
            print(f"{pressed=}")
        if released:
            print(f"{released=}")

        self.on_mouse_move(current_states)
        self.on_mouse_click(pressed, released)
        self.prev_mouse_state = current_states

    def on_mouse_click(self, pressed, released):
        clicked = 0
        if "Mouse Left Click" in pressed:
            clicked = clicked | Mouse.LEFT_BUTTON
        if "Mouse Right Click" in pressed:
            clicked |= Mouse.RIGHT_BUTTON
        if "Mouse Middle Click" in pressed:
            clicked |= Mouse.MIDDLE_BUTTON

        if clicked > 0:
            self.mouse.press(clicked)

        unclicked = 0
        if "Mouse Left Click" in released:
            unclicked = unclicked | Mouse.LEFT_BUTTON
        if "Mouse Right Click" in released:
            unclicked |= Mouse.RIGHT_BUTTON
        if "Mouse Middle Click" in released:
            unclicked |= Mouse.MIDDLE_BUTTON
        if unclicked > 0:
            self.mouse.release(unclicked)


    def on_mouse_move(self, states):
        if "Mouse Up" in states:
            self.dy = -1
        elif "Mouse Down" in states:
            self.dy = 1
        else:
            self.dy = 0
        if "Mouse Left" in states:
            self.dx = -1
        elif "Mouse Right" in states:
            self.dx = 1
        else:
            self.dx = 0

        if self.dx == 0 and self.dy == 0:
            self.acc = 3.0
        else:
            self.acc += 0.5
            self.acc = min(20, self.acc)

        if "Mouse Wheel Up" in states:
            self.dwheel = 1
        elif "Mouse Wheel Down" in states:
            self.dwheel = -1
        else:
            self.dwheel = 0
        if self.dx != 0 or self.dy != 0 or self.dwheel != 0:
            self.mouse.move(
                int(self.dx * self.acc), int(self.dy * self.acc), self.dwheel
            )


class BaseKeyboard:
    def __init__(self) -> None:
        self.uart = busio.UART(board.GP0, board.GP1, baudrate=115200)
        self.total_key_state = 0
        self.read_pins = [
            DigitalInOut(pin)
            for pin in [
                board.GP11,
                board.GP12,
                board.GP13,
                board.GP14,
                board.GP15,
            ]
        ]
        self.select_pins = [
            DigitalInOut(pin)
            for pin in [
                board.GP16,
                board.GP17,
                board.GP18,
                board.GP19,
                board.GP20,
                board.GP21,
                board.GP22,
                board.GP26,
            ]
        ]
        for pin in self.read_pins:
            pin.direction = Direction.INPUT
            pin.pull = Pull.DOWN

        for pin in self.select_pins:
            pin.direction = Direction.OUTPUT
            pin.value = False

        self.led_pin = DigitalInOut(board.LED)
        self.led_pin.direction = Direction.OUTPUT
        self.led_pin.value = True

    def led_control(self, value: bool):
        self.led_pin.value = value

    def led_toggle(self):
        self.led_pin.value = not self.led_pin.value

    def read_key_state(self):
        self.total_key_state = 0
        for selector_idx in range(len(self.select_pins)):
            self.select_pins[selector_idx - 1].value = False
            self.select_pins[selector_idx].value = True
            for key_state in [r.value for r in self.read_pins]:
                self.total_key_state = (self.total_key_state << 1) | (
                    1 if key_state else 0
                )

    def sync_key_state(self) -> bool:
        return False

    def handle_key_state(self):
        pass

    def run(self):
        count = 0
        while True:
            if count % 100 == 0:
                self.led_toggle()
            self.read_key_state()
            self.sync_key_state()
            self.handle_key_state()
            count += 1


class MasterKeyboard(BaseKeyboard):
    def __init__(self) -> None:
        super().__init__()
        self.slave_key_state = 0
        self.prev_key_state = [[False for _ in range(16)] for _ in range(5)]
        self.current_key_state = [[False for _ in range(16)] for _ in range(5)]

        self.prev_pressing_key = set()

        self.keyboard = Keyboard(usb_hid.devices)
        self.mouse = BaseMouse()

        self.is_fn_pressed = False
        self.is_right = "right" in os.listdir()
        print(f"{self.is_right=}")

    def sync_key_state(self) -> bool:
        self.uart.write(b"req")
        recved = self.uart.read(5)
        self.slave_key_state = int.from_bytes(recved, "little")
        # print(self.slave_key_state)

        for col in range(16)[::-1]:
            for row in range(5)[::-1]:
                if self.is_right:
                    if col < 8:
                        self.current_key_state[row][col] = bool(
                            self.slave_key_state & 1
                        )
                        self.slave_key_state >>= 1
                    else:
                        self.current_key_state[row][col] = bool(
                            self.total_key_state & 1
                        )
                        self.total_key_state >>= 1
                else:
                    if col < 8:
                        self.current_key_state[row][col] = bool(
                            self.total_key_state & 1
                        )
                        self.total_key_state >>= 1
                    else:
                        self.current_key_state[row][col] = bool(
                            self.slave_key_state & 1
                        )
                        self.slave_key_state >>= 1
        return True

    def handle_key_state(self):
        _p = []
        current_pressing_keys = set()
        self.is_fn_pressed = self.current_key_state[3][15]

        for row in range(5):
            for col in range(16):
                if self.current_key_state[row][col]:
                    current_pressing_keys.add(
                        FN_KEY_MAP[row][col]
                        if self.is_fn_pressed
                        else KEY_MAP[row][col]
                    )

                if self.current_key_state[row][col]:
                    _p.append(KEY_MAP[row][col])

        pressed = current_pressing_keys - self.prev_pressing_key
        released = self.prev_pressing_key - current_pressing_keys
        if Keycode.F24 in released:
            sleep(0.3)
        self.keyboard.press(*[k for k in pressed if k not in EXCLUDED_KEYS])
        self.keyboard.release(*[k for k in released if k not in EXCLUDED_KEYS])

        self.mouse.on_mouse_state(
            *(s for s in current_pressing_keys if isinstance(s, str))
        )
        self.prev_pressing_key = current_pressing_keys


class SlaveKeyboard(BaseKeyboard):
    def __init__(self) -> None:
        super().__init__()
        self.count = 0

    def sync_key_state(self) -> bool:
        if self.uart.read(3) != b"req":
            return False

        # self.total_key_state |= 1 << self.count % 40
        self.count += 1
        self.uart.write(self.total_key_state.to_bytes(5, "little"))
        return True


sleep(1)
is_master = supervisor.runtime.usb_connected
keyboard = MasterKeyboard() if is_master else SlaveKeyboard()

keyboard.run()
