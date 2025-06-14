# Imports
import requests
import json
import hmac
import hashlib
from datetime import datetime, timedelta, timezone, date
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from supabase import create_client, Client
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import os
import io
# Import AI agent's function
from ai_agent import run_ai_tailoring

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# --- Supabase Configuration ---
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(supabase_url, supabase_key)

# --- Lemon Squeezy Configuration ---
LEMONSQUEEZY_API_KEY = os.environ.get("LEMONSQUEEZY_API_KEY")
LEMONSQUEEZY_STORE_ID = os.environ.get("LEMONSQUEEZY_STORE_ID")
LEMONSQUEEZY_STANDARD_VARIANT_ID = os.environ.get("LEMONSQUEEZY_STANDARD_VARIANT_ID")
LEMONSQUEEZY_PRO_VARIANT_ID = os.environ.get("LEMONSQUEEZY_PRO_VARIANT_ID")
LEMONSQUEEZY_WEBHOOK_SECRET = os.environ.get("LEMONSQUEEZY_WEBHOOK_SECRET")
LEMONSQUEEZY_API_URL = "https://api.lemonsqueezy.com/v1"
LEMONSQUEEZY_CHECKOUT_LINK_BASE = os.environ.get("LEMONSQUEEZY_CHECKOUT_LINK", "YOUR_SINGLE_CHECKOUT_LINK_HERE") # Load base link


# --- Constants ---
FREE_PLAN_MONTHLY_LIMIT = 3
STANDARD_PLAN_MONTHLY_LIMIT = 15
# Pro plan is effectively unlimited, checked by the is_pro_plan flag


# --- Routes for Navigation (from previous steps) ---
@app.route('/')
def landing_page():
    """Renders the initial landing page for the application."""
    return render_template('landing_page.html')

@app.route('/subscriptions')
def show_subscriptions():
    """Renders the subscription packages page."""
    return render_template('subscription_packages.html')

# --- Authentication Routes ---
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    Handles user signup.
    GET: Displays the signup form.
    POST: Processes the signup form.
    """

        # If the request is a POST (user submitted the form)
    if request.method == 'POST':
        # Get email and password from the submitted form data
        email = request.form.get('email')
        password = request.form.get('password')

        # Simple validation
        if not email or not password:
            flash('Email and password are required.', 'error')
            return redirect(url_for('signup'))

        # Query the 'users' table for an entry matching the email
        existing_user_check = supabase.table('users').select('id', count='exact').eq('email', email).execute()

        # If count > 0, the email is already registered
        if existing_user_check.count > 0:
            flash('Email address already registered.', 'error')
            print(f"Signup failed: {email} already exists.")
            return redirect(url_for('signup'))

        # --- Create Lemon Squeezy Customer *Before* Supabase User ---
        # Generate a simple name from the email for LS
        name = email.split('@')[0].replace('.', '').replace('+', '')
        ls_customer_id, ls_error = create_lemon_squeezy_customer(email, name)

        # --- Create User in Supabase Database ---
        # Hash the user's password securely before storing it
        password_hash = generate_password_hash(password)

        print(f"Creating Supabase user for {email} linked to LS ID {ls_customer_id}")
        # Prepare the data for the new user row
        user_data = {
            'email': email,
            'password_hash': password_hash,
            'lemonsqueezy_customer_id': ls_customer_id,
            'is_free_plan': True, # Default to Free plan
            'is_standard_plan': False,
            'is_pro_plan': False,
            'message_count': 0,
            'messages_this_hour': 0,
            'last_message_timestamp': None,
            'messages_this_month': 0,
            'usage_reset_date': None
        }
        # Insert the new user data into the 'users' table
        insert_result = supabase.table('users').insert(user_data).execute()

    # If the request is GET (user just visiting the page), render the signup form
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles user login.
    GET: Displays the login form.
    POST: Processes the login form.
    This is a SIMPLIFIED / MOCK login. No real database check here.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username and password:
            session['logged_in'] = True
            session['username'] = username
            print(f"MOCK LOGIN: User '{username}' logged in.")
            return redirect(url_for('tailor_resume'))
        else:
            print("MOCK LOGIN FAILED: Invalid credentials.")
            return render_template('auth.html', form_type='login', error="Invalid username or password.")
    return render_template('auth.html', form_type='login')

@app.route('/logout')
def logout():
    """Logs the user out by clearing the session."""
    session.pop('logged_in', None)
    session.pop('username', None)
    print("User logged out.")
    return redirect(url_for('landing_page'))

# --- Resume Tailoring Page ---
@app.route('/tailor_resume', methods=['GET', 'POST'])
def tailor_resume():
    """
    Allows user to input job description and upload resume.
    If not logged in, redirects to login.
    GET: Displays the form.
    POST: Processes the form, calls AI, and provides download.
    """
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        job_description = request.form.get('job_description', '')
        resume_file = request.files.get('resume_file')

        if not job_description or not resume_file:
            return render_template('tailor_resume.html', error="Please provide both job description and resume file.", username=session.get('username'))

        resume_content = ""
        if resume_file.filename.endswith('.txt'):
            resume_content = resume_file.read().decode('utf-8')
        elif resume_file.filename.endswith('.docx'):
            # --- DOCX HANDLING ---
            # You'll need to install python-docx: pip install python-docx
            # from docx import Document
            # doc = Document(resume_file)
            # for para in doc.paragraphs:
            #     resume_content += para.text + "\n"
            print("WARNING: DOCX file uploaded. For this example, only .txt content is fully processed.")
            # Fallback for demo, in real app, process DOCX content properly.
            resume_content = "MOCK DOCX CONTENT from " + resume_file.filename
        else:
            return render_template('tailor_resume.html', error="Unsupported file type. Please upload a .txt or .docx file.", username=session.get('username'))

        # --- CALL YOUR ACTUAL AI AGENT FUNCTION HERE ---
        # Replace the placeholder `simulate_ai_tailoring` with `run_ai_tailoring`
        # from your ai_agent.py script.
        tailored_resume_markdown = run_ai_tailoring(job_description, resume_content)

        # Prepare the tailored resume for download
        return_data = io.BytesIO(tailored_resume_markdown.encode('utf-8'))
        return send_file(
            return_data,
            mimetype='text/markdown',
            as_attachment=True,
            download_name='tailored_resume.md'
        )

    return render_template('tailor_resume.html', username=session.get('username'))

# --- New Static Pages ---
@app.route('/privacy')
def privacy_policy():
    """Renders the Privacy Policy page."""
    return render_template('privacy.html')

@app.route('/terms')
def terms_conditions():
    """Renders the Terms & Conditions page."""
    return render_template('terms.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """
    Renders the Contact Us page and handles form submissions.
    """
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')

        print(f"--- NEW CONTACT MESSAGE ---")
        print(f"Name: {name}")
        print(f"Email: {email}")
        print(f"Subject: {subject}")
        print(f"Message: {message}")
        print(f"---------------------------")
        return render_template('contact.html', message="Your message has been sent successfully! We'll get back to you soon.")
    return render_template('contact.html')


if __name__ == '__main__':
    app.run(debug=True)
    