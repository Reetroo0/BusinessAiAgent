from fastapi import FastAPI, Request, HTTPException, Body
from pydantic import BaseModel
import uvicorn
from set_token import set_gigachat_access_token
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from main import run_agent
import json
from dotenv import find_dotenv, load_dotenv
import os
from pathlib import Path

# Определяем схему для входящих данных
class CompanyData(BaseModel):
    formalization_level: str
    automation_systems: str
    kpi_metrics: str
    data_driven_decisions: str
    it_systems_used: str
    systems_integration: str
    cloud_services_usage: str
    info_security_measures: str
    digital_literacy: str
    training_programs: str
    it_specialists_in_house: str
    employees_automation_perception: str
    it_strategy: str
    state_electronic_services: str
    future_implementation_plans: str

# Планировщик для периодического запуска функции
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    scheduler.add_job(set_gigachat_access_token, 'interval', minutes=20)
    set_gigachat_access_token()
    try:
        yield
    finally:
        scheduler.shutdown()

app = FastAPI(lifespan=lifespan)


@app.get("/digitalMaturity")
async def digital_maturity(data: CompanyData = Body(...)):
    """Accepts company data in request body (JSON) and returns agent result as JSON.

    Note: FastAPI allows body on GET when explicitly declared, but some clients/proxies
    may not support bodies for GET — consider POST if that is an issue.
    """
    company_dict = data.model_dump()

    # Save company data to src/data.json so tools in models.py can load it on demand
    src_dir = Path(__file__).parent
    data_path = src_dir / 'data.json'
    
    with data_path.open('w', encoding='utf-8') as f:
        json.dump(company_dict, f, ensure_ascii=False, indent=2)

    question = "Оцени уровень цифровой зрелости компании"
    # Load token from .env (if present) and build headers
    load_dotenv(find_dotenv())
    token = os.getenv("GIGACHAT_ACCESS_TOKEN")
    
    try:

        headers = None
        if token:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            #print(headers)

        # Do not pass company_data to run_agent; tools will read data.json
        result = run_agent(question, headers=headers)
    except Exception as e:
        #print(f"Error in /digitalMaturity: {e}")
        # Log exception server-side if needed, return 500 to client
        raise HTTPException(status_code=500, detail=str(e))

    return {"result": result}


class QuestionPayload(BaseModel):
    question: str


@app.get("/askQuestion")
@app.post("/askQuestion")
async def ask(request: Request, payload: QuestionPayload = Body(...)):
    """Accepts JSON body with {'question': '...'} and returns agent answer as JSON.

    The endpoint accepts an Authorization header (Bearer token) which will be
    forwarded to the agent initialization if present.
    """
    try:
        # Build headers dict from request (preserve Authorization if provided)
        headers = {}
        raw_auth = request.headers.get('authorization') or request.headers.get('Authorization')
        if raw_auth:
            # Normalize common issues seen in incoming Authorization header values:
            # - surrounding single or double quotes
            # - URL-encoded or whitespace artifacts
            # - ensure scheme 'Bearer ' is present
            auth = raw_auth.strip()
            # strip surrounding quotes if present
            if (auth.startswith('"') and auth.endswith('"')) or (auth.startswith("'") and auth.endswith("'")):
                auth = auth[1:-1].strip()

            # Some clients may send Authorization without scheme, only token — add 'Bearer '
            if not auth.lower().startswith('bearer '):
                # If it looks like 'Token <token>' or just raw token, try to extract token part
                parts = auth.split()
                if len(parts) == 1:
                    token = parts[0]
                else:
                    # take last part as token
                    token = parts[-1]
                auth = f'Bearer {token}'

            headers['Authorization'] = auth

        question = payload.question
        result = run_agent(question, headers=headers)
    except ValueError as ve:
        # missing token or config issues
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"result": result}



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

