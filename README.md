# **Chyrp - Social Media Platform**
Chyrp is a modern, responsive social media platform built with a FastAPI backend and vanilla JavaScript frontend. It allows users to share moments, connect with others, and express themselves through posts, likes, and comments.

## **Features**
User Authentication: Register and login with JWT token-based authentication

Post Management: Create, read, update, and delete posts with text, images, and videos

Social Interactions: Like, save, and comment on posts

User Profiles: Customizable profiles with avatars and bios

Real-time Messaging: Chat with other users

Theming System: Multiple color themes to personalize your experience

Responsive Design: Works on desktop, tablet, and mobile devices

Search Functionality: Find posts and users easily

## **Technology Stack**
### **Backend**
FastAPI: Modern, fast web framework for building APIs

SQLite: Lightweight database (can be easily switched to PostgreSQL/MySQL)

SQLAlchemy: ORM for database operations

JWT: JSON Web Tokens for authentication

Python-multipart: For handling file uploads

Pillow: Image processing capabilities

Frontend
Vanilla JavaScript: No framework dependencies

HTML5 & CSS3: Modern web standards

Font Awesome: Icons

Flexbox & Grid: Modern CSS layout techniques

## **Installation & Setup**
Prerequisites
Python 3.7+

pip (Python package manager)

A modern web browser

Backend Setup
Navigate to the backend directory:
bash
cd backend

Create a virtual environment (recommended):
bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install dependencies:
bash
pip install -r requirements.txt

Run the backend server:
bash
uvicorn main:app --reload

The backend will be available at http://localhost:8000

## **Access API documentation:**

Swagger UI: http://localhost:8000/docs

## **Frontend Setup**
Serve the frontend files using any HTTP server:

Option 1: Python HTTP server
bash
python -m http.server 3000

Option 2: Node.js serve
bash
npx serve .

Option 3: PHP server
bash
php -S localhost:3000

Open your browser and navigate to:
http://localhost:3000

## **API Endpoints**
Authentication
POST /register - Create a new user account

POST /token - Login and receive JWT token

Users
GET /users/me - Get current user profile

PUT /users/me - Update current user profile

GET /users/{username} - Get user profile by username

POST /users/{username}/follow - Follow a user

DELETE /users/{username}/follow - Unfollow a user

Posts
GET /posts - Get posts with optional filtering

POST /posts - Create a new post

GET /posts/{post_id} - Get a specific post

PUT /posts/{post_id} - Update a post

DELETE /posts/{post_id} - Delete a post

GET /users/{username}/posts - Get posts by a specific user

Interactions
POST /posts/{post_id}/like - Like a post

DELETE /posts/{post_id}/like - Unlike a post

POST /posts/{post_id}/save - Save a post

DELETE /posts/{post_id}/save - Unsave a post

GET /posts/{post_id}/comments - Get post comments

POST /posts/{post_id}/comments - Add a comment to a post

Messaging
GET /messages - Get user messages

GET /messages/{user_id} - Get conversation with a user

POST /messages/{user_id} - Send a message to a user

Search
GET /search - Search for posts or users

## **Configuration**
Environment Variables
Create a .env file in the backend directory with the following variables:

env
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=sqlite+aiosqlite:///./chyrp.db
CORS Settings

The backend is configured to allow requests from:
http://localhost:3000

http://127.0.0.1:3000

Update the origins list in main.py if you need to allow other domains.

##Usage Guide
Creating an Account
Open the application in your browser

Click on "Sign Up" or navigate to the registration form

Fill in your details: email, username, full name, and password

Submit the form to create your account

## **Creating a Post**
Log in to your account

Click the "+" icon in the navigation bar

Select the post type: Blog, Video, or Picture

Add a title, content, and category

Optionally upload media

Click "Publish" to share your post

Interacting with Posts
Like: Click the heart icon on any post

Save: Click the bookmark icon to save a post for later

Comment: View comments by clicking the comment icon

Messaging
Click the chat icon in the navigation bar

Select a user from your conversations

Type your message and press Enter or click send

Changing Themes
Click on any of the theme buttons in the navigation bar to change the color scheme:

Default: Purple and coral gradient

Coral: Orange and coral gradient

Night: Dark mode with green accents

Blossom: Pink and pastel gradient

## **Troubleshooting**
### Common Issues
CORS Errors

Ensure the backend is running on port 8000

Check that the frontend URL is in the allowed origins list

### Authentication Errors

Verify your token is being stored correctly in localStorage

Check that the token is included in request headers

### File Upload Issues

Ensure the uploads directory exists and has write permissions

Check that file size limits are appropriate for your needs

### Database Issues

Verify the database file exists and is accessible

Check that database migrations have been applied

### Debugging
Backend Logs

Check the console output from the FastAPI server for errors

Frontend Debugging

Open browser Developer Tools (F12)

Check the Console tab for JavaScript errors

Monitor the Network tab for API request/response details

### API Testing

Use the Swagger UI at http://localhost:8000/docs to test endpoints directly

## **License** 
This project is open source and available under the MIT License.



