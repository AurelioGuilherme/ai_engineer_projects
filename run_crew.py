import os

from dotenv import load_dotenv
from langfuse import get_client
from openinference.instrumentation.crewai import CrewAIInstrumentor
from openinference.instrumentation.litellm import LiteLLMInstrumentor

from src.agents.data_agent import data_agent_func
from src.agents.news_agent import news_agent_func
from src.agents.report_agent import report_agent_func
from src.crew_core import Agent, Crew

# Carrega variáveis de ambiente
load_dotenv()

# Inicializa cliente Langfuse
langfuse = get_client()

if langfuse.auth_check():
    print("Langfuse client is authenticated and ready!")
else:
    print("Authentication failed. Please check your credentials and host.")

# Inicializa instrumentação automática para tracing
CrewAIInstrumentor().instrument(skip_dep_check=True)
LiteLLMInstrumentor().instrument()

# Define agentes
agents = [
    Agent(name="DataAgent", role_description="Consulta DB e extrai métricas", func=data_agent_func),
    Agent(
        name="NewsAgent",
        role_description="Busca notícias recentes sobre SRAG",
        func=news_agent_func,
    ),
    Agent(name="ReportAgent", role_description="Gera relatório e gráficos", func=report_agent_func),
]

# Define o Crew com os agentes
crew = Crew(agents=agents)

# Executa pipeline com tracing ativo
with langfuse.start_as_current_observation(name="SRAG-Pipeline", as_type="span"):
    ctx0 = {"db_path": os.path.join(os.getcwd(), "srag.db")}
    ctx = crew.execute(initial_context=ctx0)
    print("Relatório salvo em:", ctx.get("report_path"))

# Envio dos traces para o lanfuse
langfuse.flush()
