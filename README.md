# Learning Management System 🎓

LMS is a modern, lightweight Learning Management System built with **Python** and **Flask**. It provides a complete student experience, featuring a responsive UI, real-time course searching, and automated certificate generation.

---

## 🚀 Features

* **User Authentication**: Secure signup and login system using `Werkzeug` password hashing.
* **Course Discovery**: Explore courses by category (Python, Design, Backend, etc.) with a live AJAX search bar.
* **Dynamic Dashboard**: High-level overview of enrollment statistics, including courses in progress and completed certificates.
* **Interactive Learning Interface**:
    * Video lesson player with a persistent curriculum sidebar.
    * One-click "Complete Lesson" functionality that updates progress by 25% increments.
    * Personalized note-taking system for each course.
* **Automated Certification**: Once a course reaches 100% completion, a unique certificate ID is generated and stored.
* **PDF Generation**: Earned certificates can be downloaded as professional PDFs directly from the browser using `jsPDF`.

---

## 🛠️ Technical Stack

* **Backend:** Python 3, Flask.
* **Database:** SQLite3 (Local file-based).
* **Frontend:** HTML5, Tailwind CSS, FontAwesome.
* **JavaScript Libraries:** * [jsPDF](https://github.com/parallax/jsPDF) (For client-side certificate generation).
    * Native Fetch API (For live search functionality).

---

## 📦 Installation & Setup

Follow these steps to get the project running on your local machine:

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/athena-lms.git](https://github.com/your-username/athena-lms.git)
    cd learning-management-system
    ```

2.  **Install dependencies:**
    ```bash
    pip install flask werkzeug
    ```

3.  **Run the application:**
    ```bash
    python lms_main.py
    ```
    *Note: The script is configured to initialize the database and populate it with demo courses automatically on the first run.*

4.  **Access the LMS:**
    Open your browser and navigate to `http://127.0.0.1:5000`

---

## 🔐 Demo Credentials

The database comes pre-loaded with a demo student account:
* **Email:** `user@example.com`
* **Password:** `password123`

---

## 📂 Project Structure

* `lms_main.py`: The core Flask application containing all routes, database logic, and UI templates.
* `lms_database.db`: The SQLite database (generated automatically).
* `README.md`: Project documentation.

---

## 📝 Roadmap

- [ ] Add an Instructor Dashboard to upload and manage courses.
- [ ] Implement actual video file upload and storage.
- [ ] Migrate to PostgreSQL for production deployment.

---
Developed with ✨ by Ayush Srivastava
