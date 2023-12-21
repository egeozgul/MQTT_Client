from BLE_CEEO import Listen
import time
import mqtt
import machine
#  https://www.mqtt-dashboard.com - uses their test broker

import network, ubinascii
from mySecrets import Tufts_Wireless as wifi

import sensor
import time
import image

# Configure camera
sensor.reset()
sensor.set_contrast(3)
sensor.set_gainceiling(16)
sensor.set_framesize(sensor.QVGA)
sensor.set_pixformat(sensor.GRAYSCALE)


# Get center x, y of camera image
WIDTH = sensor.width()
HEIGHT = sensor.height()
CENTER_X = int(WIDTH / 2 + 0.5)
CENTER_Y = int(HEIGHT / 2 + 0.5)


# Create cascade for finding faces
face_cascade = image.HaarCascade("frontalface", stages=25)

#sensor.reset()  # Reset and initialize the sensor.
#sensor.set_pixformat(sensor.RGB565)  # Set pixel format to RGB565 (or GRAYSCALE)
#sensor.set_framesize(sensor.QVGA)  # Set frame size to QVGA (320x240)
#sensor.skip_frames(time=2000)  # Wait for settings take effect.
clock = time.clock()  # Create a clock object to track the FPS.


def connect_wifi(wifi):
    station = network.WLAN(network.STA_IF)
    station.active(True)
    mac = ubinascii.hexlify(network.WLAN().config('mac'), ':').decode()
    print("MAC " + mac)
    station.connect(wifi['ssid'], wifi['pass'])
    while not station.isconnected():
        time.sleep(1)
    print('Connection successful')
    print(station.ifconfig())

def whenCalled(topic, msg):
    print((topic.decode(), msg.decode()))
    L.send(msg.decode())

printTimer = time.ticks_ms()

def main():
    try:
        print('L connected')
        fred = mqtt.MQTTClient('Pico', 'broker.hivemq.com', keepalive=1000)
        fred.connect()
        print('MQTT Connected')
        fred.set_callback(whenCalled)
    except OSError as e:
        print('Failed')
        return
    fred.subscribe('SPIKE')
    try:
        while L.is_connected:
            #msg = 'test'
            #fred.publish('SPIKE', "testing...")
            #time.sleep(0.5)
            fred.check_msg()  # check subscriptions - you might want to do this more often     
            
            #clock.tick()  # Update the FPS clock.
            #img = sensor.snapshot()  # Take a picture and return the image.
            #print(clock.fps())  # Note: OpenMV Cam runs about half as fast when connected
            # to the IDE. The FPS should increase once disconnected.
            
            # Take timestamp (for calculating FPS)
            clock.tick()
        
            # Take photo
            img = sensor.snapshot()
        
            # Find faces in image
            objects = img.find_features(face_cascade, threshold=0.75, scale_factor=1.25)
        
            # Find largest face in image
            largest_face_size = 0
            largest_face_bb = None
            for r in objects:
        
                # Find largest bounding box
                face_size = r[2] * r[3]
                if (face_size > largest_face_size):
                    largest_face_size = face_size
                    largest_face_bb = r
        
                # Draw bounding boxes around all faces
                img.draw_rectangle(r)
        
            # Find distance from center of face to center of frame
            if largest_face_bb is not None:
        
                # Turn on status LED
                #led.on()
        
                # Print out the largest face info
                print("Face:", largest_face_bb)
        
                # Find x, y of center of largest face in image
                face_x = largest_face_bb[0] + int((largest_face_bb[2]) / 2 + 0.5)
                face_y = largest_face_bb[1] + int((largest_face_bb[3]) / 2 + 0.5)
        
                # Draw line from center of face to center of frame
                img.draw_line(CENTER_X, CENTER_Y, face_x, face_y)
            
                if(time.ticks_ms() -  printTimer  > 250):
                    #printTimer = time.ticks_ms()
                    #print(face_x - CENTER_X)
                    if(face_x - CENTER_X > 20):
                        fred.publish('SPIKE', "right")
                    elif(face_x - CENTER_X < -20):
                        fred.publish('SPIKE', "left")
                    else:
                        fred.publish('SPIKE', "fwd")
                else:
                    fred.publish('SPIKE', "off")
            
            
            
    except Exception as e:
        print(e)
    finally: 
        fred.disconnect()
        print('done')

connect_wifi(wifi)

#led = machine.Pin('LED', machine.Pin.OUT)
L = Listen("Maria", verbose = True)
if L.connect_up():
    main()

