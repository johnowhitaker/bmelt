import sys
import time
from machine import ADC, PWM, Pin


GPIO_IDS = (26, 27, 28)
ADC_CHANNEL = {
    26: 0,
    27: 1,
    28: 2,
}
ADC_MV = 3300
SERVO_GPIO = 10
SERVO_FREQ_HZ = 50
SERVO_LEFT_US = 1000
SERVO_RIGHT_US = 2000
SERVO_PERIOD_US = 1000000 // SERVO_FREQ_HZ

pins = {}
adcs = {}
modes = {}
servo = None
servo_position = "LEFT"


def write_line(text):
    sys.stdout.write(text + "\n")
    try:
        sys.stdout.flush()
    except Exception:
        pass


def pin_name(gpio):
    return "GP%d" % gpio


def err(message):
    message = str(message).replace("\\", "\\\\").replace('"', '\\"')
    write_line('{"ok":false,"error":"%s"}' % message)


def release_pin(gpio):
    pin = pins.get(gpio)
    if pin is None:
        pin = Pin(gpio, Pin.IN, pull=None)
        pins[gpio] = pin
    else:
        pin.init(Pin.IN, pull=None)
    modes[gpio] = "Z"


def set_pin(gpio, mode):
    mode = mode.upper()
    if mode in ("Z", "IN", "INPUT", "FLOAT", "FLOATING", "HI-Z", "HIZ", "HIGHZ"):
        release_pin(gpio)
        return
    if mode in ("LOW", "0", "GND"):
        pins[gpio].init(Pin.OUT, value=0)
        modes[gpio] = "LOW"
        return
    if mode in ("HIGH", "1", "VDD", "3V3"):
        pins[gpio].init(Pin.OUT, value=1)
        modes[gpio] = "HIGH"
        return
    raise ValueError("mode must be Z, LOW, or HIGH")


def parse_pin(text):
    token = text.upper()
    if token.startswith("GP"):
        token = token[2:]
    gpio = int(token)
    if gpio not in GPIO_IDS:
        raise ValueError("pin must be GP26, GP27, or GP28")
    return gpio


def read_pin(gpio):
    digital = pins[gpio].value()
    adc_u16 = adcs[gpio].read_u16()
    mv = (adc_u16 * ADC_MV + 32767) // 65535
    return (
        '{"pin":"%s","mode":"%s","digital":%d,"adc_u16":%d,"millivolts":%d}'
        % (pin_name(gpio), modes[gpio], digital, adc_u16, mv)
    )


def read_response(target):
    if target is None:
        return '{"ok":true,"pins":[%s]}' % ",".join(read_pin(gpio) for gpio in GPIO_IDS)
    return '{"ok":true,"pin":%s}' % read_pin(target)


def servo_duty_u16(pulse_us):
    return (pulse_us * 65535 + SERVO_PERIOD_US // 2) // SERVO_PERIOD_US


def servo_set(position):
    global servo_position
    position = position.upper()
    if position == "LEFT":
        pulse_us = SERVO_LEFT_US
    elif position == "RIGHT":
        pulse_us = SERVO_RIGHT_US
    else:
        raise ValueError("servo position must be LEFT or RIGHT")
    servo.duty_u16(servo_duty_u16(pulse_us))
    servo_position = position


def servo_response():
    return (
        '{"ok":true,"servo":{"pin":"GP%d","position":"%s","left_us":%d,"right_us":%d}}'
        % (SERVO_GPIO, servo_position, SERVO_LEFT_US, SERVO_RIGHT_US)
    )


def toggle_servo():
    servo_set("RIGHT")
    time.sleep_ms(1000)
    servo_set("LEFT")
    write_line(servo_response())


def state_response(target):
    if target is None:
        states = ",".join(
            '{"pin":"%s","mode":"%s"}' % (pin_name(gpio), modes[gpio])
            for gpio in GPIO_IDS
        )
        return '{"ok":true,"pins":[%s]}' % states
    return '{"ok":true,"pin":"%s","mode":"%s"}' % (pin_name(target), modes[target])


def handle_command(line):
    parts = line.strip().split()
    if not parts:
        return

    cmd = parts[0].upper()

    if cmd in ("?", "HELP"):
        write_line(
            '{"ok":true,"commands":["PING","READ [ALL|GP26|GP27|GP28]",'
            '"STATE [ALL|GP26|GP27|GP28]","SET GP26|GP27|GP28 Z|LOW|HIGH",'
            '"RELEASE GP26|GP27|GP28","ALLZ","TOGGLE SERVO","SERVO STATE"]}'
        )
        return

    if cmd == "PING":
        write_line('{"ok":true,"reply":"pong"}')
        return

    if cmd == "TOGGLE" and len(parts) == 2 and parts[1].upper() == "SERVO":
        toggle_servo()
        return

    if cmd == "SERVO":
        if len(parts) == 2 and parts[1].upper() == "STATE":
            write_line(servo_response())
            return
        raise ValueError("usage: TOGGLE SERVO or SERVO STATE")

    if cmd in ("READ", "ADC", "DIG", "DIGITAL"):
        target = None
        if len(parts) > 1 and parts[1].upper() not in ("ALL", "*"):
            target = parse_pin(parts[1])
        write_line(read_response(target))
        return

    if cmd == "STATE":
        target = None
        if len(parts) > 1 and parts[1].upper() not in ("ALL", "*"):
            target = parse_pin(parts[1])
        write_line(state_response(target))
        return

    if cmd == "SET":
        if len(parts) != 3:
            raise ValueError("usage: SET GP26|GP27|GP28 Z|LOW|HIGH")
        if parts[1].upper() in ("ALL", "*"):
            if parts[2].upper() not in ("Z", "IN", "INPUT", "FLOAT", "FLOATING", "HI-Z", "HIZ", "HIGHZ"):
                raise ValueError("SET ALL only supports Z")
            for gpio in GPIO_IDS:
                release_pin(gpio)
            write_line(state_response(None))
            return
        gpio = parse_pin(parts[1])
        set_pin(gpio, parts[2])
        write_line(state_response(gpio))
        return

    if cmd == "RELEASE":
        if len(parts) != 2:
            raise ValueError("usage: RELEASE GP26|GP27|GP28")
        gpio = parse_pin(parts[1])
        release_pin(gpio)
        write_line(state_response(gpio))
        return

    if cmd == "ALLZ":
        for gpio in GPIO_IDS:
            release_pin(gpio)
        write_line(state_response(None))
        return

    raise ValueError("unknown command")


def init():
    global servo
    for gpio in GPIO_IDS:
        pins[gpio] = Pin(gpio, Pin.IN, pull=None)
        adcs[gpio] = ADC(ADC_CHANNEL[gpio])
        release_pin(gpio)
    servo = PWM(Pin(SERVO_GPIO))
    servo.freq(SERVO_FREQ_HZ)
    servo_set("LEFT")


init()
write_line(
    '{"ok":true,"ready":"pico-dut-gpio","pins":["GP26","GP27","GP28"],'
    '"servo":{"pin":"GP10","position":"LEFT"},"baud":921600}'
)

while True:
    try:
        command = sys.stdin.readline()
        if command:
            handle_command(command)
        else:
            time.sleep_ms(10)
    except Exception as exc:
        err(exc)
