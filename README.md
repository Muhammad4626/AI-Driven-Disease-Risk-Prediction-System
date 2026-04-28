# AI-Driven-Disease-Risk-Prediction-System
AI-Driven Disease Risk Prediction System for Post-Flood Areas in Pakistan

Authors: Muhammad Muzammil & Syed Muhammad Afaq 
Type: Bachelor’s Final Year Project (FYP)  

---

## Project Overview

This project aims to predict the risk of post-flood diseases (Cholera, Malaria, and Dengue) in flood-affected districts of Pakistan using AI models trained on historical flood and health data.

NDMA analysts can input flood and environmental data, and the system provides:
- Disease risk predictions
- SHAP-based explanations
- Visual analytics (heatmaps, graphs, trends)

## System Modules
1. Frontend
2. Backend
3. Flood Cache & Trigger 
4. AI Model 
5. Prediction & Inference
6. Explainability (SHAP)  
7. Visualization & Analytics  

---

## Deployment-ready notes (AWS + Nginx)

### Frontend (React)
- Build output: `Project-Frontend/build/`
- The frontend is designed to call the backend using **relative `/api/...`** when `REACT_APP_API_URL` is not set.
  - This is ideal for Nginx deployments where Nginx proxies `/api` to FastAPI.
- Optional: if you deploy backend on a different domain, set `REACT_APP_API_URL` at build time.

### Backend (FastAPI)
- Entry: `Project-Backend/app/main.py`
- Run behind Nginx (recommended) with:
  - `uvicorn app.main:app --host 127.0.0.1 --port 8000`
- **CORS is env-driven**:
  - Set `CORS_ORIGINS` (comma-separated), e.g.
    - Local: `http://localhost:3000,http://127.0.0.1:3000`
    - Prod: `https://your-domain.com`
- Required env vars (see `Project-Backend/.env.example`):
  - DB: `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`
  - JWT: `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`

### Runtime assets required for predictions
The backend prediction endpoint loads local artifacts:
- CatBoost models expected at `Project-Backend/models/`:
  - `malaria_model.cbm`
  - `typhoid_model.cbm`
  - `ad_model.cbm`
- Optional global SHAP images expected at `Project-Backend/global_shap/<disease>/`:
  - `summary_plot.png`
  - `importance_bar.png`

### Nginx
An example Nginx config is included at `deployment/nginx.conf`:
- Serves the React build
- Proxies `/api/*` and `/health` to `127.0.0.1:8000`

