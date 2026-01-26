Personal Developer Website - README

Instructions for Running the Website:

1. File Structure:
   - app.py (Flask application)
   - requirements.txt (Python dependencies)
   - templates/ (HTML templates)
     - base.html
     - home.html
     - projects.html
     - contact.html
   - static/ (Static files)
     - style.css
     - images/ (your image files)

2. Prerequisites:
   - Python 3.10 or higher installed

3. Setup Steps:

   a. Create a virtual environment (optional but recommended):
      python -m venv venv
      
      Windows activation:
      venv\Scripts\activate
      
      Mac/Linux activation:
      source venv/bin/activate

   b. Install dependencies:
      pip install -r requirements.txt

   c. Place your images in static/images/ folder:
      - profile.jpg (for homepage)
      - project1.jpg through project6.jpg (for projects page)

   d. Update templates with your personal information:
      - Edit home.html: Change name, position, bio
      - Edit contact.html: Update email, LinkedIn, other details
      - Edit projects.html: Update project information

4. Running the Application:

   a. Start the Flask server:
      python run.py

   b. Open your web browser and navigate to:
      http://localhost:5000

5. Access Pages:
   - Home: http://localhost:5000/
   - Projects: http://localhost:5000/projects
   - Contact: http://localhost:5000/contact

6. To Stop the Server:
   Press Ctrl+C in the terminal where the server is running

Notes:
- The navigation bar is fixed at the top of every page
- The current page is highlighted in the navigation
- The site is responsive and works on mobile devices
- All external links open in new tabs