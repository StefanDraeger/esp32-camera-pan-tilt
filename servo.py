from machine import Pin, PWM


class Servo:
    """Einfache 50-Hz-Servoansteuerung fuer MicroPython."""

    def __init__(self, pin, min_angle, max_angle, start_angle,
                 min_us=500, max_us=2500):
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.min_us = min_us
        self.max_us = max_us
        self._angle = self._limit(start_angle)
        self._pwm = PWM(Pin(pin), freq=50)
        self.write(self._angle)

    @property
    def angle(self):
        return self._angle

    def _limit(self, angle):
        return max(self.min_angle, min(self.max_angle, int(angle)))

    def write(self, angle):
        self._angle = self._limit(angle)
        span_us = self.max_us - self.min_us
        # Die Winkelgrenzen begrenzen nur die Bewegung. Die Pulsbreite wird
        # weiterhin auf den physikalischen Bereich von 0 bis 180 Grad bezogen.
        pulse_us = self.min_us + (self._angle * span_us // 180)
        self._pwm.duty_ns(pulse_us * 1000)
        return self._angle

    def move(self, difference):
        return self.write(self._angle + difference)

    def release(self):
        """PWM abschalten, ohne die zuletzt bekannte Position zu vergessen."""
        self._pwm.duty_ns(0)

    def deinit(self):
        self._pwm.deinit()
