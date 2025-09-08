try:
    import RPi.GPIO as GPIO
    _rpi = True
except ImportError:
    print("⚠️ RPi.GPIO not found — running in simulation mode.")
    _rpi = False

if _rpi:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(18, GPIO.OUT)
    pwm = GPIO.PWM(18, 1000)
    pwm.start(0)
else:
    pwm = None


def set_brightness(percentage: int):
    """
    Set LED brightness as a percentage (0–100).
    Works on Raspberry Pi, simulates otherwise.
    """
    if not 0 <= percentage <= 100:
        raise ValueError("Brightness must be between 0 and 100")

    if _rpi:
        pwm.ChangeDutyCycle(percentage)
    else:
        print(f"[Simulated] Brightness set to {percentage}%")

def cleanup():
    """
    Stop PWM and clean up GPIO.
    """
    if _rpi:
        pwm.stop()
        GPIO.cleanup()
    else:
        print("[Simulated] Cleanup complete")
