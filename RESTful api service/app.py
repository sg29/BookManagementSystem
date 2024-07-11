from flask import Flask,jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from models import Book, Review, db
import json
from confluent_kafka import Producer, KafkaException
import threading
import redis

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@localhost:5432/bookstore'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

if __name__ == '__main__':
    app.run(debug=True)

# Kafka producer configuration
kafka_conf = {
    'bootstrap.servers': 'your_broker_endpoint',  # Update with your AWS Managed Kafka broker endpoints
    'security.protocol': 'SSL',  # Depending on your Kafka configuration
    'ssl.ca.location': 'path_to_ca_cert',  # Path to CA certificate if SSL is enabled
    'ssl.certificate.location': 'path_to_client_cert',  # Path to client certificate if SSL is enabled
    'ssl.key.location': 'path_to_client_key',  # Path to client key if SSL is enabled
    'api.version.request': True
}

# Create Kafka producer
producer = Producer(kafka_conf)

# Redis connection setup
redis_host = 'your_redis_endpoint'  # Update with your ElastiCache Redis endpoint
redis_port = 6379
redis_db = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)

# Define Redis keys for caching recommendations
REDIS_RECOMMENDATIONS_KEY = 'recommendations'

# Helper function to asynchronously send messages to Kafka topic
def send_to_kafka(topic, message):
    try:
        producer.produce(topic, json.dumps(message).encode('utf-8'))
        producer.flush()  # Ensure all messages are sent
    except KafkaException as e:
        print(f"Failed to produce message: {e}")
        # Handle exception as needed

# Define Kafka topics for each endpoint
BOOKS_TOPIC = 'books_topic'
REVIEWS_TOPIC = 'reviews_topic'
RECOMMENDATIONS_TOPIC = 'RECOMMENDATIONS_TOPIC'
REVIEWS_SUMMARY_TOPIC = 'REVIEWS_SUMMARY_TOPIC'
RECOMMENDATIONS_REQUEST_TOPIC = 'RECOMMENDATIONS_REQUEST_TOPIC'

# POST /books: Add a new book
@app.route('/books', methods=['POST'])
def add_book():
    data = request.get_json()
    new_book = Book(title=data['title'], author=data['author'], genre=data['genre'],
                    year_published=data['year_published'])
    db.session.add(new_book)
    db.session.commit()
    
    # Send message to Kafka topic
    send_to_kafka(BOOKS_TOPIC, {'action': 'add', 'book': new_book.serialize()})
    
    return jsonify({'message': 'Book added successfully'}), 201

# GET /books: Retrieve all books
@app.route('/books', methods=['GET'])
def get_all_books():
    books = Book.query.all()
    return jsonify([book.serialize() for book in books]), 200

# GET /books/<id>: Retrieve a specific book by its ID
@app.route('/books/<int:id>', methods=['GET'])
def get_book_by_id(id):
    book = Book.query.get_or_404(id)
    return jsonify(book.serialize()), 200

# PUT /books/<id>: Update a book's information by its ID
@app.route('/books/<int:id>', methods=['PUT'])
def update_book(id):
    book = Book.query.get_or_404(id)
    data = request.get_json()
    book.title = data['title']
    book.author = data['author']
    book.genre = data['genre']
    book.year_published = data['year_published']
    book.summary = data['summary']
    
    # Uncomment to write to DB directly
    #db.session.commit()
    
    # Send message to Kafka topic
    send_to_kafka(BOOKS_TOPIC, {'action': 'update', 'book': book.serialize()})
    
    return jsonify({'message': 'Book updated successfully'}), 200

# DELETE /books/<id>: Delete a book by its ID
@app.route('/books/<int:id>', methods=['DELETE'])
def delete_book(id):
    book = Book.query.get_or_404(id)
    
    # Uncomment to write to DB directly
    #db.session.delete(book)
    #db.session.commit()
    
    # Send message to Kafka topic
    send_to_kafka(BOOKS_TOPIC, {'action': 'delete', 'book_id': id})
    
    return jsonify({'message': 'Book deleted successfully'}), 200

# POST /books/<id>/reviews: Add a review for a book
@app.route('/books/<int:id>/reviews', methods=['POST'])
def add_review(id):
    data = request.get_json()
    new_review = Review(book_id=id, user_id=data['user_id'], review_text=data['review_text'], rating=data['rating'])
    
    # Uncomment to write to DB directly
    #db.session.add(new_review)
    #db.session.commit()
    
    # Send message to Kafka topic
    send_to_kafka(REVIEWS_TOPIC, {'action': 'add', 'review': new_review.serialize()})
    
    return jsonify({'message': 'Review added successfully'}), 201

# GET /books/<id>/reviews: Retrieve all reviews for a book
@app.route('/books/<int:id>/reviews', methods=['GET'])
def get_reviews_by_book_id(id):
    reviews = Review.query.filter_by(book_id=id).all()
    return jsonify([review.serialize() for review in reviews]), 200

# GET /books/<id>/summary: Get a summary and aggregated rating for a book
@app.route('/books/<int:id>/summary', methods=['GET'])
def get_book_summary(id):
    book = Book.query.get_or_404(id)
    total_reviews = Review.query.filter_by(book_id=id).count()
    if total_reviews == 0:
        avg_rating = 0
    else:
        total_ratings = sum(review.rating for review in book.reviews)
        avg_rating = total_ratings / total_reviews
    summary = {
        'title': book.title,
        'author': book.author,
        'total_reviews': total_reviews,
        'avg_rating': avg_rating,
        'summary': book.summary
    }
    return jsonify(summary), 200

# GET /recommendations: Get book recommendations based on user preferences
@app.route('/recommendations', methods=['GET'])
def get_recommendations():
    # Check Redis first
    cached_recommendations = redis_db.get(REDIS_RECOMMENDATIONS_KEY)
    if cached_recommendations:
        recommendations = json.loads(cached_recommendations)
        return jsonify(recommendations), 200
    
    # If not found in Redis, query the database
    cursor.execute(f"SELECT recommended_book_id FROM recommendations where user_id={os.environ[user_id]}")
    recommendations_from_db= [row[0] for row in cursor.fetchall()]
    
    message = {
        'user_id': os.environ[user_id]
    }
    producer.produce(RECOMMENDATIONS_REQUEST_TOPIC, value=json.dumps(message))
    producer.flush()
    # Check if recommendations are found in the database
    if recommendations_from_db:
        # Cache recommendations in Redis for future requests
        redis_db.set(REDIS_RECOMMENDATIONS_KEY, json.dumps(recommendations_from_db))

        return jsonify(recommendations_from_db), 200
    else:
        return jsonify({'message': 'No recommendations found'}), 404

# POST /generate-summary: Generate a summary for a given book content
@app.route('/generate-summary', methods=['POST'])
def generate_summary():
    # Implement your summary generation logic here
    return jsonify({'message': 'Implement summary generation logic here'}), 200

if __name__ == '__main__':
    app.run(debug=True)
