from fastapi import FastAPI, Request, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Optional
import uvicorn

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

app = FastAPI()


@app.get("/digitalMaturity")
async def digital_maturity(data: CompanyData = Body(...)):
    """Accepts company data in request body (JSON) and returns agent result as JSON.

    Note: FastAPI allows body on GET when explicitly declared, but some clients/proxies
    may not support bodies for GET — consider POST if that is an issue.
    """
    company_dict = data.dict()
    # Save company data to src/data.json so tools in models.py can load it on demand
    src_dir = Path(__file__).parent
    data_path = src_dir / 'data.json'
    try:
        with data_path.open('w', encoding='utf-8') as f:
            json.dump(company_dict, f, ensure_ascii=False, indent=2)

        question = "Оцени уровень цифровой зрелости компании"
        # Load token from .env (if present) and build headers
        load_dotenv(find_dotenv())
        token = os.getenv("GIGACHAT_ACCESS_TOKEN")
        headers = None
        if token:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

        # Do not pass company_data to run_agent; tools will read data.json
        result = run_agent(question, headers=headers)
    except Exception as e:
        # Log exception server-side if needed, return 500 to client
        raise HTTPException(status_code=500, detail=str(e))

    return {"result": result}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

