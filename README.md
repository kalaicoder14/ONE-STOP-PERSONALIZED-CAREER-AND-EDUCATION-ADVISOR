# ONE-STOP-PERSONALIZED-CAREER-AND-EDUCATION-ADVISOR

# Career Guidance Platform

A Flask-based web application designed to help students discover the best career paths and colleges based on their academic performance, location, and personal interests.

## Features

- **User Authentication**: Secure registration and login for students.
- **Demographics & Academic Profile**: Collects student information, including location (district), category, and subject-wise marks.
- **Automated Cutoff Calculation**: Automatically calculates cutoff scores for various streams:
  - Engineering
  - Medical (MBBS)
  - Agriculture
  - Law, Arts & Science
- **Career Assessment**: Interactive questionnaires tailored for 10th and 12th-grade students to recommend suitable career paths.
- **College Recommendations**: Recommends colleges based on:
  - Calculated cutoffs and user categories.
  - Native and nearby district filtering.
  - specific streams (Engineering, Arts, Government Service, etc.).
- **MBBS College Predictor**: Predicts safe, target, and dream medical colleges based on expected or actual NEET scores/ranks.
- **Admin Dashboard**: Allows administrators to manage assessment questions.

## Technology Stack

- **Backend**: Python, Flask
- **Database**: MySQL (using `mysql-connector-python`)
- **Frontend**: HTML, CSS (Templates rendered via Jinja2)

## Prerequisites

- Python 3.7+
- MySQL Server

## Installation and Setup

1. **Clone the repository:**
   (Or navigate to your project directory)

2. **Install dependencies:**
   Ensure you have the required Python packages installed. You can install them using pip:
   ```bash
   pip install flask mysql-connector-python
   ```

3. **Database Configuration:**
   - Create a MySQL database named `career_guidance`.
   - Update the `db_config` dictionary in `app.py` with your MySQL credentials:
     ```python
     db_config = {
         'host': 'localhost',
         'user': 'root',
         'password': 'your_mysql_password',
         'database': 'career_guidance'
     }
     ```
   - Ensure the required tables (`users`, `demographics`, `questions`, `student_results`, `colleges`, `cutoffs`, `agri_cutoffs`, `mbbs_cutoff`, `departments`, `college_departments`) are created in your database.

4. **Run the Application:**
   ```bash
   python app.py
   ```
   Or run it using Flask directly:
   ```bash
   flask run
   ```

5. **Access the Application:**
   Open your web browser and navigate to `http://127.0.0.1:5000/`.

## Project Structure

- `app.py`: Main Flask application file containing all routes and logic.
- `templates/`: Directory containing HTML templates for the application pages.
- `static/`: Directory for static assets like CSS, JavaScript, and images.

## Usage

1. Register a new account or log in.
2. Complete the demographics profile and enter academic marks.
3. Take the 10th or 12th-grade assessment to get career recommendations.
4. Explore college lists filtered by your calculated cutoff marks, category, and preferred districts.
5. Use the specific MBBs predictor for medical colleges.
