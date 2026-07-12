# Smart Quiz

Smart Quiz is now a FastAPI + React + SQLite project with the same adaptive quiz flow as the original app.

## Stack

- Backend: FastAPI
- Server: Uvicorn
- Validation: Pydantic
- Database: SQLite with SQLAlchemy
- Frontend: React

## Project Layout

```text
quiz web/
|-- app.py
|-- backend/
|   |-- main.py
|   |-- db.py
|   |-- schemas.py
|   `-- seed_data.py
|-- frontend/
|   |-- index.html
|   |-- package.json
|   `-- src/
|       |-- App.jsx
|       |-- api.js
|       |-- main.jsx
|       `-- styles.css
|-- config.py
|-- requirements.txt
|-- schema.sql
`-- seed.sql
```

## Run It

### Backend

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

The API runs on `http://127.0.0.1:8000`.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

The React app runs on `http://localhost:5173` and talks to the FastAPI backend with cookies enabled.

## Environment Variables

Copy `.env.example` to `.env` and adjust if needed:

- `SECRET_KEY`
- `DATABASE_URL`
- `FRONTEND_ORIGINS`
- `QUESTIONS_PER_QUIZ`
- `QUIZ_TIME_SECONDS`

## Notes

- SQLite is the default database.
- SQLAlchemy keeps the database layer easy to swap later.
- The backend seeds the sample questions automatically on first run if the database is empty.
- The old Flask stack has been removed from the active project.
