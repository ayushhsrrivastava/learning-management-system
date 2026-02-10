# Learning Management System

Athena LMS 🎓
Athena LMS is a sleek, lightweight Learning Management System built with Python and Flask. It provides a complete student experience, from course exploration and progress tracking to the automated generation of completion certificates.

🚀 Features
User Authentication: Secure signup and login system using Werkzeug password hashing.

Course Discovery: Explore courses by category (Python, Design, Backend, etc.) with a real-time AJAX search bar.

Dynamic Dashboard: High-level overview of enrollment stats (Courses in progress vs. completed).

Interactive Learning:

Video lesson interface with a curriculum sidebar.

One-click "Complete Lesson" progress updates.

Personalized notes system.

Automated Certification: Once a course reaches 100% completion, a unique certificate is generated.

PDF Generation: Export earned certificates as professional PDFs directly in the browser using jsPDF.

Responsive Design: Built with Tailwind CSS, making it fully functional on desktops, tablets, and mobile devices.

🛠️ Technical Stack
Backend: Python 3, Flask

Database: SQLite3 (Local file-based)

Frontend: HTML5, Tailwind CSS, FontAwesome

JavaScript Libraries: * jsPDF (For certificate generation)

Native Fetch API (For live search)

📦 Installation & Setup
Follow these steps to get the project running on your local machine:

Clone the repository:

Bash
git clone https://github.com/your-username/athena-lms.git
cd athena-lms
Create a virtual environment (Optional but recommended):

Bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies:

Bash
pip install flask werkzeug
Run the application:

Bash
python lms_main.py
The script will automatically initialize the lms_database.db file and populate it with demo courses.

Access the LMS:
Open your browser and navigate to http://127.0.0.1:5000

🔐 Demo Credentials
You can use the pre-loaded student account to test the features immediately:

Email: user@example.com

Password: password123

📂 Project Structure
lms_main.py: The core Flask application containing all routes, database logic, and HTML templates (via render_template_string).

lms_database.db: The SQLite database (created on first run).

Template Fragments: The UI is modularized into several fragments (DASHBOARD_FRAG, EXPLORE_FRAG, etc.) for a single-page feel.

📝 Roadmap & Future Improvements
[ ] Add an Instructor Dashboard to upload new courses.

[ ] Implement actual video file uploads (currently using placeholders).

[ ] Add a "Forgot Password" email recovery system.

[ ] Migrate to a production-grade database like PostgreSQL for deployment.
