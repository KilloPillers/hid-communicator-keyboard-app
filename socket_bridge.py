import socketio
import hid_device  # import your HID functions

sio = socketio.Client()

@sio.event
def connect():
    print("Connected to server")

@sio.event
def disconnect():
    print("Disconnected from server")

@sio.on("DrawEvent")
def on_draw_event(data):
    print("Got DrawEvent from server")
    #data = hid_device.flip_horizontal(data)
    #data = hid_device.flip_vertical(data)
    data = hid_device.transform_data_for_lcd(data)
    hid_device.send_raw_report(data)

if __name__ == "__main__":
    sio.connect("https://nodejs-production-9769.up.railway.app")
    #sio.connect("http://localhost:3000")  # Adjust URL
    sio.wait()
