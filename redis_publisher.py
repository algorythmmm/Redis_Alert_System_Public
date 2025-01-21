import redis
import requests
import time

# Redis configuration
redis_host = "localhost"
redis_port = 6379
redis_channel = "sensor_data"

# API endpoint
api_url = "http://127.0.0.1:8000/api/sensor/data/1"

# Connect to Redis
redis_client = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)

def fetch_and_publish():
    while True:
        try:
            # Fetch data from the API
            response = requests.get(api_url)
            if response.status_code == 200:
                data = response.json().get("data", [])
                if data:
                    # Publish data to Redis channel
                    redis_client.publish(redis_channel, str(data[0]))
                    print(f"Published: {data[0]}")
            time.sleep(1)  # Fetch data every second
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    fetch_and_publish()
