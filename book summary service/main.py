import boto3
import psycopg2
import requests
import json
from confluent_kafka import Consumer, KafkaException

# Kafka configuration
KAFKA_CONFIG = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'book-summary-service',
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

# S3 configuration
S3_CONFIG = {
    'aws_access_key_id': 'your_access_key_id',
    'aws_secret_access_key': 'your_secret_access_key',
    'bucket_name': 'your_bucket_name'
}

# Llama3 API configuration
LLAMA3_API_URL = 'http://ec2-instance-url/llama3/api'

# Topics
BOOKS_TOPIC = 'BOOKS_TOPIC'

# Initialize Kafka consumer
consumer = Consumer(KAFKA_CONFIG)
consumer.subscribe([BOOKS_TOPIC])

# Initialize PostgreSQL connection
conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=S3_CONFIG['aws_access_key_id'],
    aws_secret_access_key=S3_CONFIG['aws_secret_access_key']
)


def get_book_metadata(book_id):
    cursor.execute("SELECT title, author, genre, year_published FROM books WHERE id=%s", (book_id,))
    return cursor.fetchone()

def get_book_contents(book_id):
    key = f'books/{book_id}.txt'
    response = s3_client.get_object(Bucket=S3_CONFIG['bucket_name'], Key=key)
    return response['Body'].read().decode('utf-8')

def send_summary_request(context):
    response = requests.post(LLAMA3_API_URL, json={'context': context})
    return response.json()['summary']
    
def upload_summary_to_s3(book_id, summary):
    summary_key = f'summaries/{book_id}_summary.txt'
    s3_client.put_object(Bucket=S3_CONFIG['bucket_name'], Key=summary_key, Body=summary)
    return summary_key


def process_books_message(message):
    action = message['action']
    book = message['book']
    
    if action in ['add', 'update']:
        book_id = book['id']
        metadata = get_book_metadata(book_id)
        contents = get_book_contents(book_id)
        
        context = f"Summary of the book in 100 words. Title: {metadata[0]}, Author: {metadata[1]}, Genre: {metadata[2]}, Year Published: {metadata[3]}. Contents: {contents}"
        summary = send_summary_request(context)
        summary_key = upload_summary_to_s3(book_id, summary)
        print(f'Summary uploaded to S3 with key: {summary_key}')

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
            
            consumer.commit(msg)

    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
