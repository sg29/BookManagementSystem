import psycopg2
import redis
import json
from confluent_kafka import Consumer, KafkaException

# Kafka configuration
KAFKA_CONFIG = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'update-data-service',
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

# Redis configuration
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0
}

# Topics
BOOKS_TOPIC = 'BOOKS_TOPIC'
REVIEWS_TOPIC = 'REVIEWS_TOPIC'
RECOMMENDATIONS_TOPIC = 'RECOMMENDATIONS_TOPIC'
REVIEWS_SUMMARY_TOPIC = 'REVIEWS_SUMMARY_TOPIC'

# Initialize Kafka consumer
consumer = Consumer(KAFKA_CONFIG)
consumer.subscribe([BOOKS_TOPIC, REVIEWS_TOPIC, RECOMMENDATIONS_TOPIC, REVIEWS_SUMMARY_TOPIC])

# Initialize PostgreSQL connection
conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

# Initialize Redis connection
redis_client = redis.StrictRedis(**REDIS_CONFIG)

def process_books_message(message):
    action = message['action']
    book = message['book']
    
    if action == 'add':
        cursor.execute("""
            INSERT INTO books (title, author, genre, year_published)
            VALUES (%s, %s, %s, %s)
        """, (book['title'], book['author'], book['genre'], book['year_published']))
    elif action == 'update':
        cursor.execute("""
            UPDATE books SET title=%s, author=%s, genre=%s, year_published=%s
            WHERE id=%s
        """, (book['title'], book['author'], book['genre'], book['year_published'], book['id']))
    elif action == 'delete':
        cursor.execute("DELETE FROM books WHERE id=%s", (book['id'],))

def process_reviews_message(message):
    review = message['review']
    
    cursor.execute("""
        INSERT INTO reviews (book_id, user_id, review_text, rating)
        VALUES (%s, %s, %s, %s)
    """, (review['book_id'], review['user_id'], review['review_text'], review['rating']))

def process_recommendations_message(message):
    user_id = message['user_id']
    recommended_book_id = message['recommended_book_id']
    
    # Update Redis cache
    redis_client.set(f'recommendations:{user_id}', recommended_book_id)

    # Update database (if necessary)
    cursor.execute("""
        INSERT INTO recommendations (user_id, recommended_book_id)
        VALUES (%s, %s)
        ON CONFLICT (user_id) DO UPDATE SET recommended_book_id = EXCLUDED.recommended_book_id
    """, (user_id, recommended_book_id))

def process_reviews_summary_message(message):
    review = message['review']
    
    cursor.execute("""
        INSERT INTO reviews_summary (book_id, review_summary, rating_summary)
        VALUES (%s, %s, %s)
    """, (review['book_id'], review['review_summary'], review['rating_summary']))

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

            if topic == BOOKS_TOPIC:
                process_books_message(message)
            elif topic == REVIEWS_TOPIC:
                process_reviews_message(message)
            elif topic == RECOMMENDATIONS_TOPIC:
                process_recommendations_message(message)
            elif topic == REVIEWS_SUMMARY_TOPIC:
                process_reviews_summary_message(message)
            
            conn.commit()
            consumer.commit(msg)

    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
