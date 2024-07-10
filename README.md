# Book Management System

<H2> Problem Statement </H2>
You are tasked with creating an intelligent book management system using Python, a locally running Llama3 generative AI model, and AWS cloud infrastructure. The system should allow users to add, retrieve, update, and delete books from a PostgreSQL database, generate summaries for books using the Llama3 model, and provide book recommendations based on user preferences. Additionally, the system should manage user reviews and generate rating and review summaries for books. The system should be accessible via a RESTful API and deployed on AWS.

<h3>Functional Requirements:</h3>
<ol>
<li>	Database Setup:
<ul><li>Use PostgreSQL to store book information.
<li>Create a books table with the following fields: id, title, author, genre, year_published, summary.
<li>Create a reviews table with the following fields: id, book_id (foreign key referencing books), user_id, review_text, rating.</ul>
<li>	Llama3 Model Integration:
<ul><li>Set up a locally running Llama3 generative AI model to generate summaries for books based on their content.
<li>Integrate the Llama3 model to generate summaries for new book entries and review summaries for each book.</ul>
<li>Machine Learning Model:
<ul><li>Develop a machine learning model to recommend books based on the genre and average rating fields.
<li>Train the model on a sample dataset of books (you can use any open dataset or generate synthetic data).</ul>
<li>RESTful API:
<ul><li>Develop a RESTful API with the following endpoints:
<ul><li>POST /books: Add a new book.
<li>GET /books: Retrieve all books.
<li>GET /books/<id>: Retrieve a specific book by its ID.
<li>PUT /books/<id>: Update a book's information by its ID.
<li>DELETE /books/<id>: Delete a book by its ID.
<li>POST /books/<id>/reviews: Add a review for a book.
<li>GET /books/<id>/reviews: Retrieve all reviews for a book.
<li>GET /books/<id>/summary: Get a summary and aggregated rating for a book.
<li>GET /recommendations: Get book recommendations based on user preferences.
<li>POST /generate-summary: Generate a summary for a given book content.
  </ul>
<li>AWS Deployment:
<ul><li>Deploy the application on AWS using services such as EC2, Lambda, or ECS.
<li>Ensure the database is hosted on AWS RDS.
<li>Use AWS S3 for storing any model files if necessary.
<li>Set up a CI/CD pipeline for automatic deployment.</ul>
<li>Authentication and Security:
<ul><li>Implement basic authentication for the API.
<li>Ensure secure communication with the database and API endpoints.</ul>
</ol>

<h3>Non Functional Requirements</h3>
<ol><li>Asynchronous Programming:
<ul><li>Implement asynchronous operations for database interactions and AI model predictions</ul>
</ol>



<h3>Architecture Diagram:</h3>
![Alt text](Architecture.png?raw=true "Architecture Diagram")
