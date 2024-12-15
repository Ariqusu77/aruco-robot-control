from .component.wheel import MotorDriver
from .component.encoder import Encoder
import time
import threading
from threading import Lock

class RobotControl:
    """
    motor PWM PINS
    motor ENB PINS
    as dict

    {
        "pwm1": 12,
        "pwm2": 18,
        "enb1": 14,
        "enb2": 15,
    }

    {
        "enc1a": 5,
        "enc1b": 6,

        "enc2a": 23,
        "enc2b": 24,
    }
    """

    left_right_ratio = 23 / 25

    def __init__(self, left, right):
        self.left_wheel = MotorDriver(
            left["pwm1"], left["pwm2"], left["enb1"], left["enb2"]
        )
        self.right_wheel = MotorDriver(
            right["pwm1"], right["pwm2"], right["enb1"], right["enb2"]
        )
        self.left_encoder = Encoder(left["enc1"], left["enc2"])
        self.right_encoder = Encoder(right["enc1"], right["enc2"])
        self.left_speed = 0
        self.right_speed = 0
        self.state = "stopped"  # Possible states: "stopped", "forward", "backward"
        self.correction_thread_running = False
        self.correction_gain = 0.1
        self.lock = Lock()
        
    def _periodic_correction(self):
        def periodic_correction():
            while True:
                with self.lock:
                    if self.state == "stopped":
                        self.correction_thread_running = False
                        break
                    self.corrrection_algorithm()
                time.sleep(0.3)

        if not self.correction_thread_running:
            self.correction_thread_running = True
            thread = threading.Thread(target=periodic_correction, daemon=True)
            thread.start()

    def corrrection_algorithm(self):
        left_ticks = self.left_encoder.getValue()
        right_ticks = self.right_encoder.getValue()

        error = left_ticks - right_ticks

        if self.state == "forward":
            self.left_speed -= error * self.correction_gain
            self.right_speed += error * self.correction_gain
            self.move_forward()
        elif self.state == "backward":
            self.left_speed -= error * self.correction_gain
            self.right_speed += error * self.correction_gain
            self.move_backward()

    def set_speed(self, left_speed, right_speed):
        self.left_speed = left_speed
        self.right_speed = right_speed

    def move_forward(self):
        with self.lock:
            self.state = "forward"
        self._periodic_correction()
        self.left_wheel.move_forward(speed=self.left_speed)
        self.right_wheel.move_forward(speed=self.right_speed)

    def move_backward(self):
        with self.lock:
            self.state = "backward"
        self._periodic_correction()
        self.left_wheel.move_backward(speed=self.left_speed)
        self.right_wheel.move_backward(speed=self.right_speed)

    def pivot_right(self):
        self.left_wheel.move_reverse(speed=self.left_speed)
        self.right_wheel.move_reverse(speed=self.right_speed)

    def pivot_left(self):
        self.left_wheel.move_forward(speed=self.left_speed)
        self.right_wheel.move_forward(speed=self.right_speed)

    def stop(self):
        with self.lock:
            self.state = "stopped"
        self.left_speed = 0
        self.right_speed = 0
        self.left_wheel.stop_moving()
        self.right_wheel.stop_moving()

    def disconnect(self):
        self.left_wheel.disconnect()
        self.right_wheel.disconnect()

    # Example compound actions
    def robot_forward(self, speed=20):
        self.set_speed(speed, speed * self.left_right_ratio)
        self.move_forward()

    def robot_backward(self, speed=25):
        self.set_speed(speed, speed * self.left_right_ratio)
        self.move_backward()

    def robot_pivot_right(self, speed=25):
        self.set_speed(speed, speed * self.left_right_ratio)
        self.pivot_right()

    def robot_pivot_left(self, speed=25):
        self.set_speed(speed, speed * self.left_right_ratio)
        self.pivot_left()
        
    def left_wheel_forward(self):
        self.left_wheel.move_forward(speed=self.left_speed)

    def left_wheel_backward(self):
        self.left_wheel.move_backward(speed=self.left_speed)

    def right_wheel_forward(self):
        self.right_wheel.move_forward(speed=self.right_speed)

    def right_wheel_backward(self):
        self.right_wheel.move_backward(speed=self.right_speed)

    def robot_left_forward(self, speed=25):
        self.set_speed(speed, 0)
        self.left_wheel_forward()

    def robot_left_backward(self, speed=25):
        self.set_speed(speed, 0)
        self.left_wheel_backward()

    def robot_right_forward(self, speed=25):
        self.set_speed(0, speed)
        self.right_wheel_forward()

    def robot_right_backward(self, speed=25):
        self.set_speed(0, speed)
        self.right_wheel_backward()