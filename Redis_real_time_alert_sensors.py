from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from redis import Redis
import time
import random
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, message_queue='redis://localhost:6379/0')  # Point to your Redis instance
redis = Redis.from_url('redis://localhost:6379/0')  # Connect to Redis

@app.route('/')
def index():
    # Retrieve the query parameters
    resident_name = request.args.get('resident_name')
    house_id = request.args.get('house_id')
    address = request.args.get('address')
    resident_id = request.args.get('resident_id')
    sensor = request.args.get('sensor')  # Get the sensor number

    print(f"Resident Name: {resident_name}, House ID: {house_id}, Address: {address}, Resident ID: {resident_id}, Sensor: {sensor}")

    # Render the template with the passed parameters
    return render_template('index.html', 
                           resident_name=resident_name,
                           house_id=house_id,
                           address=address,
                           resident_id=resident_id,
                           sensor=sensor)

@socketio.on('connect')
def handle_connect():
    print("Client connected")

# Example to send temperature data and publish to Redis
def send_temperature():
    while True:
        temperature_data = {
            'value': random.randint(15, 30),  # Example data
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        # Publish to Redis channel
        redis.publish('temperature_channel', str(temperature_data))
        time.sleep(1)  # Update every second

@socketio.on('message', namespace='/temperature')
def handle_temperature_message(message):
    print('Received message: ' + message)

# Thread to listen to Redis messages and emit them to clients
def listen_to_redis():
    pubsub = redis.pubsub()
    pubsub.subscribe('temperature_channel')

    for message in pubsub.listen():
        if message['type'] == 'message':
            data = eval(message['data'])  # Convert string back to dictionary
            socketio.emit('temperature_update', data)  # Emit to connected clients

if __name__ == '__main__':
    # Start the Redis listener in a background thread
    threading.Thread(target=listen_to_redis).start()
    socketio.start_background_task(send_temperature)  # Start the temperature update task
    socketio.run(app, host='0.0.0.0', port=8080)
