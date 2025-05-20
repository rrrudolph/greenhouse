import time
from machine import Pin, PWM, ADC, Timer
from rotary_irq_rp2 import RotaryIRQ  

FT_LIGHTS = PWM(Pin(1, Pin.OUT))
GH_LIGHTS = PWM(Pin(2, Pin.OUT))
GH_LIGHTS.freq(1000)
FT_LIGHTS.freq(1000)
# LIGHT_POT = ADC(Pin(27))
# BOOST_POT = ADC(Pin(28))
MOISTURE_SENSOR = ADC(Pin(26))

LEDS_RELAY = Pin(3, Pin.OUT) # Relay 1
PUMP_RELAY = Pin(5, Pin.OUT) # Relay 2
DRIPLINE = Pin(4, Pin.OUT)   # Relay 3
MOISTURE_SENSOR_POWER = Pin(0, Pin.OUT)

FT_LIGHT_MULTIPLIER = 1.4  # seems a little dimmer than I wanted

SW=Pin(10,Pin.IN,Pin.PULL_UP)  
r = RotaryIRQ(pin_num_dt=11,   
        pin_num_clk=12,   
        min_val=0,   
        reverse=False,   
        range_mode=RotaryIRQ.RANGE_BOUNDED) 
 
val_old = r.value()

def turn_pump_off(timer):
    print("Turning pump OFF")
    global pump_timer_on
    pump_timer_on = False
    PUMP_RELAY.off() 

pump_timer_on = False
def turn_pump_on(timer):
    print("Turning pump ON")
    global pump_timer_on
    pump_timer_on = True
    PUMP_RELAY.on() 

    # Set up another timer to turn the pump OFF after 5 minutes
    t0 = Timer(period=5 * 60 * 1000, mode=Timer.ONE_SHOT, callback=turn_pump_off)

# Set up a timer to turn the pump ON every hour
def start_hourly_timer():
    t1 = Timer(period=60 * 60 * 1000, mode=Timer.PERIODIC, callback=turn_pump_on)

def turn_dripline_off(timer):
    print("Turning dripline OFF")
    DRIPLINE.off()

def turn_dripline_on():
    print("Turning dripline ON")
    DRIPLINE.on() 

    # Set up a timer to turn the dripline OFF after 30 minutes
    t3 = Timer(period=30 * 60 * 1000, mode=Timer.ONE_SHOT, callback=turn_dripline_off)

def read_moisture_sensor(timer):
    MOISTURE_SENSOR_POWER.on()
    time.sleep(1)
    # 57000 == dry air
    # 48000 == in moist soil but without good contact
    # 42000 == in moist soil with good contact
    moisture_reading = MOISTURE_SENSOR.read_u16()
    if moisture_reading > 52000:
        turn_dripline_on()
    
    MOISTURE_SENSOR_POWER.off()

def start_moisture_sensor_timer(hours=1):
    t00 = Timer(period=hours * 60 * 60 * 1000, mode=Timer.PERIODIC, callback=read_moisture_sensor)

start_hourly_timer()
start_moisture_sensor_timer()

while True:  
    try:  
        val_new = r.value() 
        # Button click will be used to manually toggle the pump
        if SW.value()==0 and n==0:  
            print("Button Pressed")
            # Only allow the pump to be toggled if it's not currently ON due to the timer
            if not pump_timer_on:
                PUMP_RELAY.toggle()

            n=1  
            while SW.value()==0:  
                continue  
        n=0  
        if val_old != val_new:  
            val_old = val_new  
            print('result =', val_new)  
        
        if val_new > 0:
            LEDS_RELAY.on()
            GH_LIGHTS.duty_u16(val_new)
            FT_LIGHTS.duty_u16(min(int(val_new * FT_LIGHT_MULTIPLIER), 65000)) 
        else:
            LEDS_RELAY.off()
            GH_LIGHTS.duty_u16(0)
            FT_LIGHTS.duty_u16(0)

#         # do sound boosting
#         boost_strength = BOOST_POT.read_u16()
#         sound_signal = MOISTURE_SENSOR.read_u16()

#         # split up the 0-65000 range into +/- for either boosting or dimming. 20000 will be used as 0 point
#         # if boost_strength > 20000:
#         #     GH_LIGHTS.duty_u16(led_strength + sound_signal + (boost_strength - 20000))
        time.sleep_ms(50)  

    except KeyboardInterrupt:  
        break

