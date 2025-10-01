import sys
sys.path.append('..')

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_gigachat.chat_models import GigaChat
from langchain.schema.messages import HumanMessage
from models import analyze_digital_maturity, recommend_it_solutions, show_all_IT_solutions, show_all_available_support
from typing import Dict, Optional
import json

from dotenv import find_dotenv, load_dotenv
import os
import threading

# Загрузка переменных окружения (файл .env при старте)
load_dotenv(find_dotenv())

# Ленивая инициализация агента, чтобы можно было подставлять токен (например из headers)
_AGENT_LOCK = threading.Lock()
_AGENT = None
_AGENT_TOKEN = None

system_prompt = (
    "Ты являешься виртуальным помощником («Цифровым консультантом для бизнеса" 
    "»), работающим в рамках Департамента цифрового развития, информационных технологий и связи. "
    "Основная цель твоего существования — помощь предпринимателям малого и среднего бизнеса (МСБ) "
    "в области цифровизации их организаций путем предоставия квалифицированной консультации и рекомендаций по следующим направлениям: "
    "оценка текущего уровня цифровой зрелости компании, предложение конкретных ИТ-решений (CRM, ERP, СЭД и другие), "
    "выбор наиболее подходящих мер господдержки (субсидии, гранты и прочие программы помощи МСБ)."
)

TOOLS = [analyze_digital_maturity, recommend_it_solutions, show_all_IT_solutions, show_all_available_support]


def _init_agent(token: str):
    """Create and return a new agent configured with the provided token."""
    # Устанавливаем переменную окружения, которую использует библиотека GigaChat
    os.environ["GIGACHAT_CREDENTIALS"] = token
    # Инициализируем модель и агента
    model = GigaChat(model="GigaChat-2", verify_ssl_certs=False)
    agent = create_react_agent(model, tools=TOOLS, checkpointer=MemorySaver(), prompt=system_prompt)
    return agent


def _get_agent(headers: Optional[Dict] = None):
    """Return a cached agent; initialize if not present or token changed.

    headers: optional dict that may contain 'Authorization': 'Bearer <token>'
    """
    global _AGENT, _AGENT_TOKEN

    # extract token: prefer Authorization header, fallback to env
    token = None
    if headers:
        auth = headers.get("Authorization") or headers.get("authorization")
        if auth and isinstance(auth, str) and auth.lower().startswith("bearer "):
            token = auth.split(None, 1)[1].strip()

    if not token:
        token = os.getenv("GIGACHAT_ACCESS_TOKEN")

    if token is None or len(token.strip()) == 0:
        raise ValueError("Variable GIGACHAT_ACCESS_TOKEN is missing or empty.")

    with _AGENT_LOCK:
        if _AGENT is None or _AGENT_TOKEN != token:
            # ensure environment variable used by GigaChat library is set
            os.environ["GIGACHAT_CREDENTIALS"] = token
            _AGENT = _init_agent(token)
            _AGENT_TOKEN = token
    return _AGENT


def run_agent(question: str, company_data: Optional[Dict] = None, headers: Optional[Dict] = None) -> str:
    """Invoke the agent with a question and optional company_data and headers.

    company_data, if provided, will be attached as a JSON-formatted HumanMessage
    so tools can access it during tool execution. If headers contain an Authorization
    bearer token, it will be used to initialize the agent.
    """
    agent = _get_agent(headers)

    # If company data is provided, embed it in the question text to avoid
    # the model/client interpreting it as a structured property (which can
    # trigger strict schema validation on the Gigachat side).
    if company_data is not None:
        try:
            # create a short human-readable block from the dict
            pairs = [f"{k}: {v}" for k, v in company_data.items()]
            data_block = "\n".join(pairs)
            full_question = f"{question}\n\nКомпания (данные):\n{data_block}"
        except Exception:
            # fallback to raw JSON string
            full_question = f"{question}\n\nКомпания (данные):\n{json.dumps(company_data, ensure_ascii=False)}"
        messages = [HumanMessage(content=full_question)]
    else:
        messages = [HumanMessage(content=question)]

    config = {"configurable": {"thread_id": 1}}
    # debug output of messages if requested via env
    if os.getenv("DEBUG_AGENT_PAYLOAD"):
        print("DEBUG: outgoing messages:")
        for m in messages:
            print("---")
            print(m.content)

    resp = agent.invoke({"messages": messages}, config=config)
    answer = resp["messages"][-1].content
    return answer


__all__ = ["run_agent"]
