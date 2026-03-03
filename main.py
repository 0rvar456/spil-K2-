from machine import Pin, PWM
import neopixel
import time
import urandom

# ---------- PINNAR ----------
PIN_NEOPIXEL = 18
NUM_LEDS     = 45

BUTTON_PIN   = 13
BUZZER_PIN   = 14

# ---------- STILLINGAR ----------
DEBOUNCE_MS = 40
STEP_MS     = 20

SPIN_MIN_MS = 2000
SPIN_MAX_MS = 5000

BLINK_MS      = 120
STOP_BLINK_MS = 3000

START_SOUND_MS = 7000
BRIGHT = 80

# ---------- SETUP ----------
np = neopixel.NeoPixel(Pin(PIN_NEOPIXEL, Pin.OUT), NUM_LEDS)
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

buzzer = PWM(Pin(BUZZER_PIN))
buzzer.duty_u16(0)

def scale(grb, s):
    return (grb[0]*s//255, grb[1]*s//255, grb[2]*s//255)

OFF  = (0, 0, 0)
BLUE = scale((0, 0, 255), BRIGHT)

def clear_ring():
    np.fill(OFF)
    np.write()

def show_one(pos):
    np.fill(OFF)
    np[pos % NUM_LEDS] = BLUE
    np.write()

def pressed():
    if button.value() == 0:
        time.sleep_ms(DEBOUNCE_MS)
        return button.value() == 0
    return False

def wait_release(pin):
    while pin.value() == 0:
        time.sleep_ms(10)

def rand_between(a, b):
    return a + (urandom.getrandbits(16) % (b - a + 1))

# ======================================================
# 🎵 STARTING LAG (spilar sjálfkrafa við power-on) ~7 sek
# ======================================================
MELODY = [
    659, 784, 988, 1319,
    1175, 988, 784, 659,
    784, 988, 1319, 1568,
    1319, 988, 784, 0,
]
NOTE_MS = 110       # hraðara
START_DUTY = 17000  # punchy

def play_start_sound():
    end = time.ticks_add(time.ticks_ms(), START_SOUND_MS)
    i = 0
    while time.ticks_diff(end, time.ticks_ms()) > 0:
        f = MELODY[i % len(MELODY)]
        if f == 0:
            buzzer.duty_u16(0)
        else:
            buzzer.freq(f)
            buzzer.duty_u16(START_DUTY)
        time.sleep_ms(NOTE_MS)
        i += 1
    buzzer.duty_u16(0)

# ======================================================
# 🔊 SPIN NOISE (hljóðmengun á meðan spinn er)
# ======================================================
SPIN_DUTY = 12000

def spin_noise_step(step):
    if (step % 5) == 0:
        f = rand_between(900, 4500)
    else:
        f = 900 + ((step * 73) % 3200)
    buzzer.freq(f)
    buzzer.duty_u16(SPIN_DUTY)

def buzz_off():
    buzzer.duty_u16(0)

# ======================================================
# 🎉 WIN SOUND (skemmtilegt á meðan stop/blikk)
# ======================================================
WIN = [988, 1175, 1319, 1568, 1760, 1568, 0, 1568, 1760, 2093]
WIN_MS = 90
WIN_DUTY = 14000

def win_step(i):
    f = WIN[i % len(WIN)]
    if f == 0:
        buzzer.duty_u16(0)
    else:
        buzzer.freq(f)
        buzzer.duty_u16(WIN_DUTY)

# ======================================================
# 🔄 SPIN ROUND
# ======================================================
def run_spin():
    spin_ms = rand_between(SPIN_MIN_MS, SPIN_MAX_MS)
    spin_end = time.ticks_add(time.ticks_ms(), spin_ms)

    pos = rand_between(0, NUM_LEDS - 1)
    step = 0

    # SPIN + hljóðmengun
    while time.ticks_diff(spin_end, time.ticks_ms()) > 0:
        spin_noise_step(step)
        show_one(pos)
        pos = (pos + 1) % NUM_LEDS
        step += 1
        time.sleep_ms(STEP_MS)

    stop_pos = (pos - 1) % NUM_LEDS

    # STOP/BLINK 3 sek + win sound
    blink_end = time.ticks_add(time.ticks_ms(), STOP_BLINK_MS)
    on = True
    i = 0
    next_note = time.ticks_ms()

    while time.ticks_diff(blink_end, time.ticks_ms()) > 0:
        now = time.ticks_ms()
        if time.ticks_diff(now, next_note) >= 0:
            win_step(i)
            i += 1
            next_note = time.ticks_add(now, WIN_MS)

        if on:
            show_one(stop_pos)
        else:
            clear_ring()
        on = not on
        time.sleep_ms(BLINK_MS)

    buzz_off()
    clear_ring()

# ======================================================
# MAIN
# ======================================================
clear_ring()

# ✅ Starting lag fer sjálfkrafa í gang þegar switchinn kveikir á ESP32
play_start_sound()

print("READY")

while True:
    if pressed():
        wait_release(button)
        run_spin()
        print("READY")
    time.sleep_ms(10)
