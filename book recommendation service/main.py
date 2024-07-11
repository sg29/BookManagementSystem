import psycopg2
import requests
import json
from confluent_kafka import Consumer, Producer, KafkaException

# Kafka configuration
KAFKA_CONFIG = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'recommendation-service',
    'auto.offset.reset': 'earliest'
}

# PostgreSQL configuration
DB_CONFIG = {
    'dbname': 'your_database',
    'user': 'your_user',
    'password': 'your_password',
    'host': 'localhost',
    'port': 5432
}

# ML Model API configuration
ML_MODEL_API_URL = 'http://ec2-instance-url/ml_model/api'

# Topics
RECOMMENDATIONS_REQUEST_TOPIC = 'RECOMMENDATIONS_REQUEST_TOPIC'
RECOMMENDATIONS_TOPIC = 'RECOMMENDATIONS_TOPIC'

# Initialize Kafka consumer and producer
consumer = Consumer(KAFKA_CONFIG)
producer = Producer(KAFKA_CONFIG)
consumer.subscribe([RECOMMENDATIONS_REQUEST_TOPIC])

# Initialize PostgreSQL connection
conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

def get_all_users():
    cursor.execute("SELECT user_id FROM users")
    return cursor.fetchall()

def send_recommendation_request(user_id):
    response = requests.post(ML_MODEL_API_URL, json={'user_id': user_id})
    return response.json()['recommended_book_id']

def publish_recommendation_to_kafka(user_id, recommended_book_id):
    message = {
        'user_id': user_id,
        'recommended_book_id': recommended_book_id
    }
    producer.produce(RECOMMENDATIONS_TOPIC, value=json.dumps(message))
    producer.flush()

def process_recommendation_message(message):
    user_id = message['user_id']
    recommended_book_id = send_recommendation_request(user_id)
    publish_recommendation_to_kafka(user_id, recommended_book_id)

def batch_process_users():
    users = get_all_users()
    total_users = len(users)
    batch_size = total_users // 5
    
    for i in range(batch_size):
        user_id = users[i][0]
        recommended_book_id = send_recommendation_request(user_id)
        publish_recommendation_to_kafka(user_id, recommended_book_id)

def main():
    try:
        
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaException._PARTITION_EOF:
                    continue
                else:
                    print(msg.error())
                    break

            message = json.loads(msg.value().decode('utf-8'))
            topic = msg.topic()

            if topic == RECOMMENDATIONS_REQUEST_TOPIC:
                process_recommendation_message(message)
            
            consumer.commit(msg)

    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
