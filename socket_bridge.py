import socketio
import hidapi_device as hid_device # import your HID functions

sio = socketio.Client()
interface = None

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
    if interface:
        hid_device.send_raw_report(interface, data, True)

if __name__ == "__main__":
    interface = hid_device.get_raw_hid_interface()
    sio.connect("https://nodejs-production-9769.up.railway.app")
    #sio.connect("http://localhost:3000")  # Adjust URL
    sio.wait()
