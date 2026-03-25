# Smart Quiz

Smart Quiz is a Flask + MySQL project that gives users a timed quiz with adaptive difficulty.

## Features

- User signup, login, and logout
- Timed quiz with one shared countdown for the full attempt
- Adaptive difficulty: easy -> medium -> hard based on performance
- Dashboard showing quiz history and basic performance stats
- Clean Flask structure using Blueprints

## Tech Stack

- Python
- Flask
- MySQL
- HTML, CSS, JavaScript
- Jinja2 templates

## Project Structure

```text
quiz web/
|-- app.py
|-- config.py
|-- requirements.txt
|-- schema.sql
|-- seed.sql
|-- routes/
|   |-- auth.py
|   |-- dashboard.py
|   `-- quiz.py
|-- static/
|   |-- css/
|   `-- js/
|-- templates/
`-- utils/
    |-- adaptive.py
    `-- db.py
```

## How the Adaptive Difficulty Works

- The quiz starts with an easy question.
- A correct answer moves the next question one level up.
- A wrong answer moves the next question one level down.
- The difficulty stays inside the range: easy, medium, hard.

## Setup

### 1. Create and activate a virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Create your environment file

Copy `.env.example` to `.env` and update the password for your MySQL setup.

### 4. Create the database and seed the questions

Run the SQL files in MySQL:

```sql
SOURCE schema.sql;
SOURCE seed.sql;
```

### 5. Start the app

```powershell
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

## Environment Variables

The app reads these values from `.env`:

- `SECRET_KEY`
- `DB_HOST`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `QUESTIONS_PER_QUIZ`
- `QUIZ_TIME_SECONDS`

## What This Project Shows

- Flask application factory pattern
- Modular routing with Blueprints
- Session-based quiz logic
- MySQL database integration
- Basic full-stack web development with authentication

## Future Improvements

- Add automated tests
- Add category-based quizzes
- Add an admin page to manage questions
- Deploy with a production-ready server

## License

Built for learning purpose by Aryan Tomar
