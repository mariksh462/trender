# Trender

TR&er is a local AI-assisted social content planner. It stores a user profile, pulls current trend signals, and generates video ideas with the bundled GGUF model.

## Setup

Install the Python dependencies from the repository root:

```bash
python -m pip install -r requirements.txt
```

The backend uses PostgreSQL via `psycopg`. By default it connects to:

```text
postgresql://username:password@127.0.0.1:5432/trender
```

If needed, adjust `src/.env` before starting the app.

## Run

Start the backend:

```bash
python src/main.py
```

Serve the frontend separately:

```bash
python -m http.server 8000 --directory src/FrontEnd
```

Open the dashboard in your browser:

```text
http://127.0.0.1:8000/index.html
```

## Flow

Registration creates the session and sends the user to the profile form. Login now checks whether a profile already exists: if it does, the user goes straight to the dashboard; otherwise the profile form opens. The dashboard also includes a clickable Trending Now card that opens a modal with the top trends.

## Trends

Trend collection is implemented in `src/trends_api.py` using RSS, Reddit, TikTok, and Instagram sources.