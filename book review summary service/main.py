import psycopg2
import requests
import json
from confluent_kafka import Consumer, Producer, KafkaException

# Kafka configuration
KAFKA_CONFIG = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'review-summary-service',
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

# Llama3 API configuration
LLAMA3_API_URL = 'http://ec2-instance-url/llama3/api'

# Topics
REVIEWS_TOPIC = 'REVIEWS_TOPIC'
REVIEWS_SUMMARY_TOPIC = 'REVIEWS_SUMMARY_TOPIC'

# Initialize Kafka consumer and producer
consumer = Consumer(KAFKA_CONFIG)
producer = Producer(KAFKA_CONFIG)
consumer.subscribe([REVIEWS_TOPIC])

# Initialize PostgreSQL connection
conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()


def get_reviews_and_ratings(book_id):
    cursor.execute("SELECT review_text, rating FROM reviews WHERE book_id=%s", (book_id,))
    return cursor.fetchall()

def send_summary_request(context):
    response = requests.post(LLAMA3_API_URL, json={'context': context})
    return response.json()['summary']
    
def publish_summary_to_kafka(book_id, review_summary, rating_summary):
    message = {
        'action': 'add',
        'review': {
            'book_id': book_id,
            'review_summary': review_summary,
            'rating_summary': rating_summary
        }
    }
    producer.produce(REVIEWS_SUMMARY_TOPIC, value=json.dumps(message))
    producer.flush()
    
def process_reviews_message(message):
    review = message['review']
    book_id = review['book_id']
    
    reviews_and_ratings = get_reviews_and_ratings(book_id)
    reviews_text = " ".join([r[0] for r in reviews_and_ratings])
    average_rating = sum(r[1] for r in reviews_and_ratings) / len(reviews_and_ratings)

    context = f"Create a summary of reviews and ratings in less than 50 words. Reviews: {reviews_text}. Average Rating: {average_rating}"
    review_summary = send_summary_request(context)
    
    publish_summary_to_kafka(book_id, review_summary, f"Average Rating: {average_rating:.2f}")

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

            if topic == REVIEWS_TOPIC and message['action'] == 'add':
                process_reviews_message(message)
            
            consumer.commit(msg)

    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
