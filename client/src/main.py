"""Flask web application with MSAL authentication and blog API integration.

This module provides the main Flask application with routes for:
- OAuth authentication flow
- User profile display
- Blog post CRUD operations
"""

from __future__ import annotations

import logging
import secrets
from functools import wraps
from typing import Any, Callable

from flask import (
    Flask,
    flash,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)

from .api_client import APIClient
from .auth import MSALAuthClient
from .config import get_settings
from .exceptions import (
    APIClientError,
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)
from .models import BlogPostCreate, BlogPostUpdate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
settings = get_settings()
app.secret_key = settings.flask_secret_key

# Initialize MSAL and API clients
auth_client = MSALAuthClient(settings)
api_client = APIClient(settings)


def login_required(f: Callable) -> Callable:
    """Decorator to require authentication for routes.

    Args:
        f: Route function to wrap

    Returns:
        Wrapped function that checks for authentication
    """

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if "user" not in session:
            flash("Please sign in to access this page", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def get_access_token() -> str | None:
    """Get valid access token from session or refresh if needed.

    Returns:
        Access token string or None if not available
    """
    # First, try to get from session
    if "access_token" in session:
        return session["access_token"]

    # Try silent token acquisition
    result = auth_client.acquire_token_silent()
    if result and "access_token" in result:
        session["access_token"] = result["access_token"]
        return result["access_token"]

    return None


@app.route("/")
def index() -> str:
    """Home page route.

    Returns:
        Rendered HTML template
    """
    user = session.get("user")
    is_authenticated = user is not None

    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Blog Client - MSAL Certificate Auth</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .header {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }
            .button {
                display: inline-block;
                padding: 10px 20px;
                background-color: #0078d4;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                margin-right: 10px;
            }
            .button:hover {
                background-color: #106ebe;
            }
            .button-secondary {
                background-color: #6c757d;
            }
            .button-secondary:hover {
                background-color: #5a6268;
            }
            .flash-message {
                padding: 15px;
                margin-bottom: 20px;
                border-radius: 4px;
            }
            .flash-success {
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            .flash-error {
                background-color: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            .flash-warning {
                background-color: #fff3cd;
                color: #856404;
                border: 1px solid #ffeaa7;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔐 Blog Client Application</h1>
            <p>MSAL Python with Certificate-Based Authentication</p>
            
            {% if is_authenticated %}
                <p>Welcome, <strong>{{ user.name }}</strong>!</p>
                <a href="{{ url_for('profile') }}" class="button">View Profile</a>
                <a href="{{ url_for('list_posts') }}" class="button">Blog Posts</a>
                <a href="{{ url_for('logout') }}" class="button button-secondary">Sign Out</a>
            {% else %}
                <p>Please sign in to access the blog application.</p>
                <a href="{{ url_for('login') }}" class="button">Sign In with Microsoft</a>
            {% endif %}
        </div>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash-message flash-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <div class="header">
            <h2>About This Application</h2>
            <p>This is a demonstration of:</p>
            <ul>
                <li>MSAL Python with X.509 certificate authentication</li>
                <li>OAuth 2.0 Authorization Code Flow with PKCE</li>
                <li>Calling a protected FastAPI downstream API</li>
                <li>Blog post CRUD operations with user delegation</li>
            </ul>
        </div>
    </body>
    </html>
    """

    return render_template_string(
        template,
        is_authenticated=is_authenticated,
        user=user,
    )


@app.route("/login")
def login() -> Any:
    """Initiate OAuth authentication flow.

    Returns:
        Redirect to Microsoft authorization endpoint
    """
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(16)
    session["auth_state"] = state

    # Get authorization URL
    auth_url, _ = auth_client.get_authorization_url(state=state)

    logger.info("Redirecting to Microsoft login")
    return redirect(auth_url)


@app.route("/callback")
def callback() -> Any:
    """Handle OAuth callback from Microsoft.

    Returns:
        Redirect to home page or error page
    """
    # Verify state to prevent CSRF
    state = request.args.get("state")
    if state != session.get("auth_state"):
        logger.error("State mismatch - possible CSRF attack")
        flash("Authentication failed: Invalid state parameter", "error")
        return redirect(url_for("index"))

    # Check for errors
    if "error" in request.args:
        error = request.args.get("error")
        error_description = request.args.get("error_description", "Unknown error")
        logger.error(f"Authentication error: {error} - {error_description}")
        flash(f"Authentication failed: {error_description}", "error")
        return redirect(url_for("index"))

    # Get authorization code
    code = request.args.get("code")
    if not code:
        logger.error("No authorization code in callback")
        flash("Authentication failed: No authorization code received", "error")
        return redirect(url_for("index"))

    try:
        # Exchange code for token
        result = auth_client.acquire_token_by_authorization_code(code)

        # Store token and user info in session
        session["access_token"] = result["access_token"]

        # Extract user info from ID token claims
        id_token_claims = result.get("id_token_claims", {})
        session["user"] = {
            "name": id_token_claims.get("name", "Unknown User"),
            "preferred_username": id_token_claims.get("preferred_username", ""),
            "oid": id_token_claims.get("oid", ""),
        }

        logger.info(f"User authenticated: {session['user']['name']}")
        flash("Successfully signed in!", "success")
        return redirect(url_for("index"))

    except AuthenticationError as e:
        logger.error(f"Token acquisition failed: {e}")
        flash(f"Authentication failed: {str(e)}", "error")
        return redirect(url_for("index"))


@app.route("/logout")
def logout() -> Any:
    """Sign out the current user.

    Returns:
        Redirect to home page
    """
    user_name = session.get("user", {}).get("name", "User")

    # Clear session
    session.clear()

    # Clear MSAL cache
    auth_client.clear_cache()

    logger.info(f"User signed out: {user_name}")
    flash("Successfully signed out", "success")
    return redirect(url_for("index"))


@app.route("/profile")
@login_required
def profile() -> str:
    """Display user profile from API.

    Returns:
        Rendered HTML template
    """
    access_token = get_access_token()
    if not access_token:
        flash("Session expired. Please sign in again.", "warning")
        return redirect(url_for("login"))

    try:
        user_profile = api_client.get_profile(access_token)

        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Profile</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .card {
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                }
                .button {
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #0078d4;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                }
                .button:hover {
                    background-color: #106ebe;
                }
                .info-row {
                    display: flex;
                    padding: 10px 0;
                    border-bottom: 1px solid #eee;
                }
                .info-label {
                    font-weight: bold;
                    width: 200px;
                }
                .info-value {
                    flex: 1;
                    color: #333;
                }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>👤 User Profile</h1>
                
                <div class="info-row">
                    <div class="info-label">Name:</div>
                    <div class="info-value">{{ profile.name or 'Not set' }}</div>
                </div>
                
                <div class="info-row">
                    <div class="info-label">Email:</div>
                    <div class="info-value">{{ profile.email or 'Not set' }}</div>
                </div>
                
                <div class="info-row">
                    <div class="info-label">Preferred Username:</div>
                    <div class="info-value">{{ profile.preferred_username or 'Not set' }}</div>
                </div>
                
                <div class="info-row">
                    <div class="info-label">Object ID (OID):</div>
                    <div class="info-value">{{ profile.oid }}</div>
                </div>
                
                <div style="margin-top: 20px;">
                    <a href="{{ url_for('index') }}" class="button">← Back to Home</a>
                    <a href="{{ url_for('list_posts') }}" class="button">View Blog Posts</a>
                </div>
            </div>
        </body>
        </html>
        """

        return render_template_string(template, profile=user_profile)

    except UnauthorizedError:
        flash("Session expired. Please sign in again.", "warning")
        return redirect(url_for("logout"))
    except APIClientError as e:
        logger.error(f"Failed to fetch profile: {e}")
        flash(f"Failed to load profile: {str(e)}", "error")
        return redirect(url_for("index"))


@app.route("/posts")
@login_required
def list_posts() -> str:
    """List all blog posts.

    Returns:
        Rendered HTML template
    """
    access_token = get_access_token()
    if not access_token:
        flash("Session expired. Please sign in again.", "warning")
        return redirect(url_for("login"))

    try:
        # Get pagination parameters
        skip = request.args.get("skip", 0, type=int)
        limit = request.args.get("limit", 10, type=int)

        posts_data = api_client.list_posts(access_token, skip=skip, limit=limit)

        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Blog Posts</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .card {
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                }
                .button {
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #0078d4;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    margin-right: 10px;
                }
                .button:hover {
                    background-color: #106ebe;
                }
                .button-success {
                    background-color: #28a745;
                }
                .button-success:hover {
                    background-color: #218838;
                }
                .post-item {
                    padding: 15px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    margin-bottom: 15px;
                    background-color: #fafafa;
                }
                .post-title {
                    font-size: 1.3em;
                    font-weight: bold;
                    margin-bottom: 10px;
                }
                .post-meta {
                    color: #666;
                    font-size: 0.9em;
                    margin-bottom: 10px;
                }
                .post-content {
                    margin-top: 10px;
                    line-height: 1.6;
                }
                .pagination {
                    display: flex;
                    justify-content: space-between;
                    margin-top: 20px;
                }
                .flash-message {
                    padding: 15px;
                    margin-bottom: 20px;
                    border-radius: 4px;
                }
                .flash-success {
                    background-color: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                }
                .flash-error {
                    background-color: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                }
                .flash-warning {
                    background-color: #fff3cd;
                    color: #856404;
                    border: 1px solid #ffeaa7;
                }
            </style>
        </head>
        <body>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="flash-message flash-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <div class="card">
                <h1>📝 Blog Posts</h1>
                <p>Total posts: {{ posts_data.total }}</p>
                
                <div>
                    <a href="{{ url_for('index') }}" class="button">← Back to Home</a>
                    <a href="{{ url_for('create_post_form') }}" class="button button-success">+ Create New Post</a>
                </div>
            </div>
            
            {% if posts_data.posts %}
                {% for post in posts_data.posts %}
                    <div class="post-item">
                        <div class="post-title">{{ post.title }}</div>
                        <div class="post-meta">
                            By {{ post.author.display_name if post.author else 'Unknown' }} 
                            | {{ post.created_at.strftime('%Y-%m-%d %H:%M UTC') }}
                        </div>
                        <div class="post-content">
                            {{ post.content[:200] }}{% if post.content|length > 200 %}...{% endif %}
                        </div>
                        <div style="margin-top: 10px;">
                            <a href="{{ url_for('view_post', post_id=post.id) }}" class="button">Read More</a>
                        </div>
                    </div>
                {% endfor %}
                
                <div class="pagination">
                    <div>
                        {% if skip > 0 %}
                            <a href="{{ url_for('list_posts', skip=max(0, skip - limit), limit=limit) }}" class="button">← Previous</a>
                        {% endif %}
                    </div>
                    <div>
                        {% if skip + limit < posts_data.total %}
                            <a href="{{ url_for('list_posts', skip=skip + limit, limit=limit) }}" class="button">Next →</a>
                        {% endif %}
                    </div>
                </div>
            {% else %}
                <div class="card">
                    <p>No blog posts yet. <a href="{{ url_for('create_post_form') }}">Create the first one!</a></p>
                </div>
            {% endif %}
        </body>
        </html>
        """

        return render_template_string(
            template, posts_data=posts_data, skip=skip, limit=limit, max=max
        )

    except UnauthorizedError:
        flash("Session expired. Please sign in again.", "warning")
        return redirect(url_for("logout"))
    except APIClientError as e:
        logger.error(f"Failed to fetch posts: {e}")
        flash(f"Failed to load posts: {str(e)}", "error")
        return redirect(url_for("index"))


@app.route("/posts/<int:post_id>")
@login_required
def view_post(post_id: int) -> str:
    """View a single blog post.

    Args:
        post_id: Blog post ID

    Returns:
        Rendered HTML template
    """
    access_token = get_access_token()
    if not access_token:
        flash("Session expired. Please sign in again.", "warning")
        return redirect(url_for("login"))

    try:
        post = api_client.get_post(access_token, post_id)

        # Check if current user is the author
        current_user_oid = session.get("user", {}).get("oid", "")
        is_author = post.author and post.author.oid == current_user_oid

        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ post.title }}</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    max-width: 900px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .card {
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                }
                .button {
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #0078d4;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    margin-right: 10px;
                }
                .button:hover {
                    background-color: #106ebe;
                }
                .button-warning {
                    background-color: #ffc107;
                    color: #000;
                }
                .button-warning:hover {
                    background-color: #e0a800;
                }
                .button-danger {
                    background-color: #dc3545;
                }
                .button-danger:hover {
                    background-color: #c82333;
                }
                .post-meta {
                    color: #666;
                    font-size: 0.95em;
                    margin-bottom: 20px;
                    padding-bottom: 15px;
                    border-bottom: 1px solid #eee;
                }
                .post-content {
                    line-height: 1.8;
                    font-size: 1.1em;
                    white-space: pre-wrap;
                }
                .flash-message {
                    padding: 15px;
                    margin-bottom: 20px;
                    border-radius: 4px;
                }
                .flash-success {
                    background-color: #d4edda;
                    color: #155724;
                }
                .flash-error {
                    background-color: #f8d7da;
                    color: #721c24;
                }
            </style>
        </head>
        <body>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="flash-message flash-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <div class="card">
                <h1>{{ post.title }}</h1>
                
                <div class="post-meta">
                    <strong>Author:</strong> {{ post.author.display_name if post.author else 'Unknown' }}<br>
                    <strong>Published:</strong> {{ post.created_at.strftime('%Y-%m-%d %H:%M UTC') }}<br>
                    {% if post.updated_at != post.created_at %}
                        <strong>Last updated:</strong> {{ post.updated_at.strftime('%Y-%m-%d %H:%M UTC') }}
                    {% endif %}
                </div>
                
                <div class="post-content">{{ post.content }}</div>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                    <a href="{{ url_for('list_posts') }}" class="button">← Back to Posts</a>
                    {% if is_author %}
                        <a href="{{ url_for('edit_post_form', post_id=post.id) }}" class="button button-warning">✏️ Edit</a>
                        <a href="{{ url_for('delete_post', post_id=post.id) }}" 
                           class="button button-danger"
                           onclick="return confirm('Are you sure you want to delete this post?');">🗑️ Delete</a>
                    {% endif %}
                </div>
            </div>
        </body>
        </html>
        """

        return render_template_string(template, post=post, is_author=is_author)

    except NotFoundError:
        flash("Post not found", "error")
        return redirect(url_for("list_posts"))
    except UnauthorizedError:
        flash("Session expired. Please sign in again.", "warning")
        return redirect(url_for("logout"))
    except APIClientError as e:
        logger.error(f"Failed to fetch post: {e}")
        flash(f"Failed to load post: {str(e)}", "error")
        return redirect(url_for("list_posts"))


@app.route("/posts/new", methods=["GET", "POST"])
@login_required
def create_post_form() -> Any:
    """Create a new blog post.

    Returns:
        Rendered HTML template or redirect
    """
    if request.method == "GET":
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Create Post</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    max-width: 900px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .card {
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .form-group {
                    margin-bottom: 20px;
                }
                label {
                    display: block;
                    font-weight: bold;
                    margin-bottom: 5px;
                }
                input[type="text"], textarea {
                    width: 100%;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    font-family: inherit;
                    font-size: 1em;
                }
                textarea {
                    min-height: 300px;
                    resize: vertical;
                }
                .button {
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #0078d4;
                    color: white;
                    text-decoration: none;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 1em;
                    margin-right: 10px;
                }
                .button:hover {
                    background-color: #106ebe;
                }
                .button-secondary {
                    background-color: #6c757d;
                }
                .button-secondary:hover {
                    background-color: #5a6268;
                }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>✍️ Create New Post</h1>
                
                <form method="POST">
                    <div class="form-group">
                        <label for="title">Title:</label>
                        <input type="text" id="title" name="title" required maxlength="200">
                    </div>
                    
                    <div class="form-group">
                        <label for="content">Content:</label>
                        <textarea id="content" name="content" required></textarea>
                    </div>
                    
                    <div>
                        <button type="submit" class="button">Publish Post</button>
                        <a href="{{ url_for('list_posts') }}" class="button button-secondary">Cancel</a>
                    </div>
                </form>
            </div>
        </body>
        </html>
        """
        return render_template_string(template)

    # POST request - create the post
    access_token = get_access_token()
    if not access_token:
        flash("Session expired. Please sign in again.", "warning")
        return redirect(url_for("login"))

    try:
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()

        if not title or not content:
            flash("Title and content are required", "error")
            return redirect(url_for("create_post_form"))

        post_data = BlogPostCreate(title=title, content=content)
        new_post = api_client.create_post(access_token, post_data)

        logger.info(f"Created post {new_post.id}: {new_post.title}")
        flash("Post created successfully!", "success")
        return redirect(url_for("view_post", post_id=new_post.id))

    except UnauthorizedError:
        flash("Session expired. Please sign in again.", "warning")
        return redirect(url_for("logout"))
    except APIClientError as e:
        logger.error(f"Failed to create post: {e}")
        flash(f"Failed to create post: {str(e)}", "error")
        return redirect(url_for("create_post_form"))


@app.route("/posts/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post_form(post_id: int) -> Any:
    """Edit an existing blog post.

    Args:
        post_id: Blog post ID

    Returns:
        Rendered HTML template or redirect
    """
    access_token = get_access_token()
    if not access_token:
        flash("Session expired. Please sign in again.", "warning")
        return redirect(url_for("login"))

    try:
        post = api_client.get_post(access_token, post_id)

        if request.method == "GET":
            template = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Edit Post</title>
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        max-width: 900px;
                        margin: 0 auto;
                        padding: 20px;
                        background-color: #f5f5f5;
                    }
                    .card {
                        background: white;
                        padding: 30px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }
                    .form-group {
                        margin-bottom: 20px;
                    }
                    label {
                        display: block;
                        font-weight: bold;
                        margin-bottom: 5px;
                    }
                    input[type="text"], textarea {
                        width: 100%;
                        padding: 10px;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                        font-family: inherit;
                        font-size: 1em;
                    }
                    textarea {
                        min-height: 300px;
                        resize: vertical;
                    }
                    .button {
                        display: inline-block;
                        padding: 10px 20px;
                        background-color: #0078d4;
                        color: white;
                        text-decoration: none;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                        font-size: 1em;
                        margin-right: 10px;
                    }
                    .button:hover {
                        background-color: #106ebe;
                    }
                    .button-secondary {
                        background-color: #6c757d;
                    }
                    .button-secondary:hover {
                        background-color: #5a6268;
                    }
                    .flash-message {
                        padding: 15px;
                        margin-bottom: 20px;
                        border-radius: 4px;
                    }
                    .flash-error {
                        background-color: #f8d7da;
                        color: #721c24;
                    }
                </style>
            </head>
            <body>
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="flash-message flash-{{ category }}">{{ message }}</div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                
                <div class="card">
                    <h1>✏️ Edit Post</h1>
                    
                    <form method="POST">
                        <div class="form-group">
                            <label for="title">Title:</label>
                            <input type="text" id="title" name="title" value="{{ post.title }}" required maxlength="200">
                        </div>
                        
                        <div class="form-group">
                            <label for="content">Content:</label>
                            <textarea id="content" name="content" required>{{ post.content }}</textarea>
                        </div>
                        
                        <div>
                            <button type="submit" class="button">Update Post</button>
                            <a href="{{ url_for('view_post', post_id=post.id) }}" class="button button-secondary">Cancel</a>
                        </div>
                    </form>
                </div>
            </body>
            </html>
            """
            return render_template_string(template, post=post)

        # POST request - update the post
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()

        if not title or not content:
            flash("Title and content are required", "error")
            return redirect(url_for("edit_post_form", post_id=post_id))

        post_data = BlogPostUpdate(title=title, content=content)
        updated_post = api_client.update_post(access_token, post_id, post_data)

        logger.info(f"Updated post {updated_post.id}")
        flash("Post updated successfully!", "success")
        return redirect(url_for("view_post", post_id=post_id))

    except NotFoundError:
        flash("Post not found", "error")
        return redirect(url_for("list_posts"))
    except ForbiddenError:
        flash("You don't have permission to edit this post", "error")
        return redirect(url_for("view_post", post_id=post_id))
    except UnauthorizedError:
        flash("Session expired. Please sign in again.", "warning")
        return redirect(url_for("logout"))
    except APIClientError as e:
        logger.error(f"Failed to update post: {e}")
        flash(f"Failed to update post: {str(e)}", "error")
        return redirect(url_for("edit_post_form", post_id=post_id))


@app.route("/posts/<int:post_id>/delete")
@login_required
def delete_post(post_id: int) -> Any:
    """Delete a blog post.

    Args:
        post_id: Blog post ID

    Returns:
        Redirect to posts list
    """
    access_token = get_access_token()
    if not access_token:
        flash("Session expired. Please sign in again.", "warning")
        return redirect(url_for("login"))

    try:
        api_client.delete_post(access_token, post_id)
        logger.info(f"Deleted post {post_id}")
        flash("Post deleted successfully", "success")
        return redirect(url_for("list_posts"))

    except NotFoundError:
        flash("Post not found", "error")
        return redirect(url_for("list_posts"))
    except ForbiddenError:
        flash("You don't have permission to delete this post", "error")
        return redirect(url_for("list_posts"))
    except UnauthorizedError:
        flash("Session expired. Please sign in again.", "warning")
        return redirect(url_for("logout"))
    except APIClientError as e:
        logger.error(f"Failed to delete post: {e}")
        flash(f"Failed to delete post: {str(e)}", "error")
        return redirect(url_for("list_posts"))


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=settings.flask_port,
        debug=settings.debug,
    )
