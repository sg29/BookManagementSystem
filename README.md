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
<img src=https://github.com/sg29/BookManagementSystem/blob/main/Architecture.png>

<h3>Architecture Decisions:</h3>
<ol>
  <li>Networking:
    <ul><li>All traffic would route through an networking - ingress/egress account (having public subnet) which would validate the request and route the request to application account using transit gateway.
      <li>The application account would host 3 private subnets for service, data and analytics to better manage resources within them. 
    </ul>
  <li>Security:
    <ul><li>Cloudflare would be used as firewall for all incoming traffic.
      <li>API Gateway will authenticate each API request and check for rate limiting.
      <li>All Ec2 instances would be in there respective Security Groups (SG) with network flow restricted to limited resources.
      <li>Database SG will be accessible only from SGs accessing it.
      <li>Kafka SG will be accessible only from SGs accessing it.
      <li>The database and Kafka access will be authenticated and authorized using AWS IAM Role.
      <li>The request to Sagemaker will be authenticated and authorized using AWS IAM Role.
      <li>Access to S3 bucket will be managed using VPC endpoint and AWS IAM Role.
    </ul>
  <li>AWS Services selection:
    <ul><li>AWS API Gateway- To authenticate and authorize all incoming API requests
     <li>EC2- All microservices will be deployed on EC2. The Ec2 will use Golden AMIs which will be pre-hardened for security and packages installed.
       <li>RDS PostgreSQL with 2 read replicas- The master instance will handle the write load on database. One read instances will handle the read load for application and the other for analytics use cases (which will be read heavy).
         <li>AWS Managed Kafka Streaming Service- To increase reliability of data being delivered in case of failures and take advantage of AWS managed service.
           <li>AWS Elastic Cache- To cache recommendations.
          <li>Sagemaker- To host the ML Model</ul>
  <li>Microservices: 
    The microservices architecture will be used to develop the following services:
    <ul>
      <li>RESTful API Service:
        <ul><li>This service will be responsible to accept all incoming API requests from API Gateway
          <li>The data read requests (GET) will be fetched from RDS (postgres) and returned
          <li>The data update requests (PUT,POST,DELETE) will be written to respective Kafka topic.
          <li>The uploaded files will be writtent to S3.
        </ul>  
      <li>Update data service:
      <ul><li>This service will be responsible for polling Kafka brokers and identifying changes in each Kafka topic.
        <li>Make changes to data in database as present in the Kafka topic.
        <li>Delete message from topic.
          <li>The service will also be responsible for managing the cache in elastic cache.
      </ul>
    <li>Book Summary service:
      <ul><li>This service will be responsible for polling Kafka brokers and track if any new book or a new version of book is published.
        <li>The service will then build the context for LLM and send the request to Llama3.
          <li>The response from Llama3 will be published back in another Kakfa topic. 
          <li>The data in Kafka is then processed by Update data service and written to database.     
      </ul>
    <li>Book Review Summary service:
      <ul><li>This service will be responsible for polling Kafka brokers and track if any new review is published.
        <li>The service will then build the context for LLM and send the request to Llama3.
          <li>The response from Llama3 will be published back in another Kakfa topic. 
          <li>The data in Kafka is then processed by Update data service and written to database.     
      </ul>
    <li>Book Recommendation service:
      <ul><li>This service will be responsible for polling Kafka brokers and check if any new recommendation request is received. Batch also enabled timely.
        <li>The service will then build the context for LLM using user's previous ratings and genres and send the request to Llama3.
          <li>The response from Llama3 will be published back in another Kakfa topic. 
          <li>The data in Kafka is then processed by Update data service and written to database.     
      </ul>
  </ul>  
  
  <li>Scalability and High Availability
    <ul>
      <li>All Ec2 instances will be a part of auto-scaling group with 70% threshold for scaling-out and 30% threshold for scaling-in. Minimum instances will be 2 at any point of time in 2 different Availability Zones (AZs).
        <li>RDS will have 2 Read replicas in 2 different AZs to support any disruption due to AZ downtime.
          <li>Kafka cluster will have borkers across 2 AZs maintaining 3 replicas of data at any point of time.
            <li>S3 acceleration if needed to support faster upload and retrieval of files.
    </ul>
<li> Disaster Recovery
  <ul>
    <li>RDS data to be backed up. Delta daily and weekly full backup. The backup stored in backup vault to prevent accidental deletion of backup.
  </ul>
 <li> Devops (deployment and Maintenance) 
   <ul>
     <li>Terraform Templates to provision all infrastructure
       <li>Jenkins and Puppet for CI/CD and Configuration management respectively.
         <li>Setup and maintenance of Golden AMIs.
   </ul>
   <li> Recommendations Model
     <ul>
       <li>Collaborative Recommender System to provide recommendations on the basis of what other users with similar interests liked.
     </ul>
     <li>LLM: Llama3
     <ul>
       <li>Use of Llama3 70B model
         <li>Development of RAG to enrich context.
          <li>Guardrails to prevent misuse
     </ul>  
</ol>
