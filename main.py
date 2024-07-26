from machine import Pin
import utime
import buzzer
import stepper
import hcsr04
import math
from ssd1306 import SSD1306_I2C
from machine import SoftI2C
import mpu6050

# LED pin
led_pin = Pin(12, Pin.OUT)

# Button pin
button_pin = Pin(27, Pin.IN, Pin.PULL_UP)

# Buzzer object
buzzer1 = buzzer.Buzzer(15)

# 2 steppers and their controllers
stepper_mode = 'FULL_STEP'
left_step_pin = Pin(13, Pin.OUT, Pin.PULL_DOWN)
right_step_pin = Pin(19, Pin.OUT, Pin.PULL_DOWN)
null_pin = Pin(0, Pin.OUT, Pin.PULL_DOWN)
stepper_left = stepper.Stepper(stepper_mode, left_step_pin, null_pin, null_pin, null_pin, 10)
stepper_right = stepper.Stepper(stepper_mode, right_step_pin, null_pin, null_pin, null_pin, 10)

# Ultrasonic sensor
trigger_pin = Pin(5, Pin.OUT, Pin.PULL_DOWN)
echo_pin = Pin(18, Pin.IN, Pin.PULL_DOWN)
us_sensor = hcsr04.HCSR04(trigger_pin, echo_pin)

# OLED 
i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
oled = SSD1306_I2C(width = 128, height = 64, i2c = i2c)

# Accelerometer
accelerometer = mpu6050.accel(i2c)

# Function that waits for a button press
def wait_button_press(pause = 0.05):
    while button_pin.value() == 1:
        utime.sleep(pause)

# Sizes of letters in the OLED
XS = 8
YS = 11 #10

# Function to display text in the OLED
def display(text, x, y, xs = XS, ys = YS):
    oled.text(text, x * xs, y * ys)

# Function to display text in the OLED in a centered way
def display_centered(text, y, xs = XS, ys = YS, line_width = 16):
    x = math.floor(0.5 * (line_width - len(text)))
    display(text, x, y, xs, ys)

# Function to display "Press button to start" in the OLED
def press_button_to_start():
    oled.fill(0)
    display_centered("PRESS", 0)
    display_centered("BUTTON", 1)
    display_centered("TO", 2)
    display_centered("START", 3)
    display_centered("THE", 4)
    display_centered("SIMULATION", 5)
    oled.show()

# Function to setup the ESP32
def setup():
    print("ESP32 was started.")
    led_pin.off()
    button_pin.on()    

# Function to compute the steps from distance
def get_steps_from_distance(distance_cm, tire_radius_cm = 3, steps_per_full_revolution = 200):
    tire_circumference = 2 * math.pi * tire_radius_cm
    return math.floor((distance_cm * steps_per_full_revolution) / tire_circumference)

# Function to go forward 1 step
def one_step():
    stepper_left.step(1)
    stepper_right.step(1)

# Function to read the Y component of the accelerometer
def read_AcY():
    acc_values = accelerometer.get_values()
    return acc_values["AcY"]

# Function to show the distance and steps in the OLED
def show_distance_and_steps(distance_cm, n_steps):
    oled.fill(0)
    display_centered("Distance:", 0)
    display_centered("{} cm".format(distance_cm), 1)
    display_centered("Steps:", 3)
    display_centered("{}".format(n_steps), 4)
    oled.show()

# Function to show a centered message in the OLED
def show_message(message):
    oled.fill(0)
    display_centered(message, 2)
    oled.show()

# Function to compute and show the steps corresponding to many distances
def compute_steps():
    text = "distance,steps\n"
    for distance in range(10, 110, 10):
        steps = get_steps_from_distance(distance)
        text += "{},{}\n".format(distance, steps)
    print("Distances and steps were computed:")
    print(text)

# Function to behave in a reached state
def reached_state():
    show_message("REACHED")
    buzzer1.beep_once()

# Function to behave in a tilted state
def tilted_state():
    led_pin.on()
    show_message("TILTED")
    buzzer1.beep_once()
    utime.sleep(0.500)
    buzzer1.beep_once()
    utime.sleep(0.500)
    buzzer1.beep_once()
        
# main function
def main():
    # Initial steps
    setup()
    compute_steps()
    # Main loop
    while True:
        led_pin.off()
        press_button_to_start()
        wait_button_press()        
        buzzer1.beep_once()
        distance_cm = us_sensor.distance_cm()
        n_steps = get_steps_from_distance(distance_cm)
        show_distance_and_steps(distance_cm, n_steps)
        reached = True
        # Each step sent as a command is equivalent as 2 real steps.
        # That's why I'm dividing n_steps by 2.
        for step in range(n_steps // 2):
            one_step()
            AcY = read_AcY()
            if abs(AcY) > 12000:
                reached = False
                break
        if reached:
            reached_state()
        else:
            tilted_state()
        utime.sleep(5)        

# Execute the main function
if __name__ == "__main__":
    main()  