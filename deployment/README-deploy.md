# Deployment guide — ReportMaster AI

This folder contains templates and instructions for deploying the backend (FastAPI) to Render and the frontend (static) to Vercel.

Backend (Render)
- Use `deployment/render.yaml` as a starter template for Render.
- In Render: Create a new Web Service, connect your GitHub repo, pick branch `main`.
- Set the build command to `pip install -r requirements.txt` and start command to:

```bash
gunicorn -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:$PORT --workers 1
```

- Add environment variables in Render dashboard (example):
  - `APP_ENV=production`
  - `GROQ_API_KEY=<your key>`
  - `FRONTEND_URL=https://your-frontend.vercel.app`
  - `ALLOW_ORIGIN=https://your-frontend.vercel.app`

Frontend (Vercel)
- Import repository into Vercel and set project root to repository root.
- Configure a static deployment using `app/frontend` as the static source.
- Sample `deployment/vercel.json` forces static serving from `app/frontend`.
- Set environment variable `VITE_API_URL` in Vercel to your Render backend URL.

Local testing
- Create and activate your virtualenv, install deps:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

- Start backend locally:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Open `app/frontend/index.html` in a browser (or serve it with `python -m http.server` from that folder) and set API calls to `http://localhost:8000/api/v1`.

Notes & next steps
- Fill secret values in Render/Vercel dashboards; do not commit secrets into repository.
- Consider adding a GitHub Actions workflow to run tests and optionally deploy on push to `main`.
