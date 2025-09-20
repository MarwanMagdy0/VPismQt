try:
    import RPi.GPIO as GPIO
    _rpi = True
except ImportError:
    print("⚠️ RPi.GPIO not found — running in simulation mode.")
    _rpi = False

if _rpi:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(23, GPIO.OUT)
    buzzer = GPIO.PWM(23, 1000)  # default frequency = 1000 Hz
    buzzer_started = False
else:
    buzzer = None
    buzzer_started = False


def beep(frequency: int = 1000, duration: float = 0.2):
    """
    Make the buzzer beep at a given frequency and duration.
    frequency: in Hz (e.g. 440 = A note, 1000 = typical beep)
    duration: in seconds (float)
    """
    import time

    if _rpi:
        global buzzer_started
        if not buzzer_started:
            buzzer.start(50)  # 50% duty cycle (on)
            buzzer_started = True
        buzzer.ChangeFrequency(frequency)
        time.sleep(duration)
        buzzer.stop()
        buzzer_started = False
    else:
        print(f"[Simulated] Beep at {frequency} Hz for {duration} sec")


def buzzer_cleanup():
    """
    Clean up GPIO after use.
    """
    if _rpi:
        buzzer.stop()
        GPIO.cleanup()
    else:
        print("[Simulated] Cleanup complete")


# Example usage
if __name__ == "__main__":
    beep(1000, 0.2)  # short beep
    beep(1500, 0.3)  # higher beep
    cleanup()
