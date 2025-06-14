from flask import Flask, render_template, request, redirect, url_for, session, send_file
import io
import os
# Import your AI agent's function
from ai_agent import run_ai_tailoring

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

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
        username = request.form['username']
        password = request.form['password'] # In real app, hash this!
        session['logged_in'] = True
        session['username'] = username
        print(f"MOCK SIGNUP: User '{username}' signed up and logged in.")
        return redirect(url_for('tailor_resume'))
    return render_template('auth.html', form_type='signup')

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
    