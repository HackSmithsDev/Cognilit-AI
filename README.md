🚀 CogniLit AI: Professional Research & Learning Mentor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**CogniLit AI** is a sophisticated, containerized Flask application designed to serve as an AI-powered tutor. It features real-time chat with Gemini AI, Markdown support, voice recognition, and automated Text-to-Speech (TTS) capabilities.

🛠 Features
Dual Context AI: Switches between "General Assistant" and "Chapter Tutor" based on user navigation.

Voice Integration: Speech-to-Text (STT) for inputs and Text-to-Speech (TTS) for AI responses.

Premium UI: Modern "Pill" design with dynamic button swapping (Mic/Send).

Rate Limiting: Redis-backed protection to manage API costs and prevent abuse.

Robust Backend: PostgreSQL for persistent storage of projects, sessions, and chat history.

🏗 Setup & Installation
Option 1: The Docker Way (Recommended)

This is the fastest way to get the Database, Redis, and App running perfectly synced.

1. **Clone the repository:**

Bash
git clone [https://github.com/tushar6076/CogniLit-AI.git](https://github.com/tushar6076/CogniLit-AI.git)
cd CogniLit-AI
Configure Environment:
Create a .env file and add your keys (see Environment Variables section below).

2. **Launch the Stack:**

Bash
docker compose up --build -d

The default development configuration creates the database tables on startup. For a production deployment with a new, empty database, set `FLASK_CONFIG=production` in `.env` and apply migrations before serving requests:

```bash
docker compose exec web flask db upgrade
```

For an existing database created by the development auto-create flow, back it up and verify that its schema matches the current models before recording the baseline with `docker compose exec web flask db stamp head`. This records migration state without changing existing tables or data.
Option 2: The Manual Way (Local Development)

Use this for rapid UI/JS development.

3. **Create Virtual Environment:**

Bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
Install Dependencies:

Bash
pip install -r requirements.txt
Database & Redis:
Ensure you have PostgreSQL and Redis server running locally.

In development mode, the app creates the database tables on startup. For a new, empty database in production, apply migrations before serving requests:

```bash
FLASK_CONFIG=production flask db upgrade
```

For an existing database created by the development auto-create flow, back it up and verify that its schema matches the current models before running `FLASK_CONFIG=production flask db stamp head`. This records migration state without changing existing tables or data.
Start App:

Bash
python wsgi.py
🔑 Environment Variables (.env)
Create a file named .env in the root folder. Never commit this file to version control.

Code snippet
SECRET_KEY=your_super_secret_key
DATABASE_URI=postgresql://user:password@localhost:5432/cognilit_db
REDIS_URL=redis://localhost:6379/0
GEMINI_API_KEY=your_google_gemini_api_key
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
📂 Project Structure
/app: Core application logic (Models, Blueprints, Static/JS).

config.py: Configuration classes for Dev/Prod.

wsgi.py: The entry point for the application.

Dockerfile / docker-compose.yml: Containerization settings.
migrations/: Database schema migrations.

requirements.txt: Python dependencies.

🧪 **Tests**

Install the development and test dependencies, then run the Flask test suite:

```bash
python -m pip install -r requirements-dev.txt
pytest
```

`tests/conftest.py` provides an isolated SQLite database, Flask test client, and sample user fixture. Tests do not require Docker, PostgreSQL, Redis, or live email/AI credentials.

🧪 **Commands Cheat Sheet**
Task	Command
Build & Run	docker compose up --build
Stop App	docker compose down
New Migration	FLASK_CONFIG=production flask db migrate -m "description"
View Logs	docker compose logs -f web
Interactive Shell	flask shell