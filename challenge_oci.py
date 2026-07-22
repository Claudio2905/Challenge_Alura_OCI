import os
from dotenv import load_dotenv

load_dotenv()  # carga las variables desde .env
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

from langchain_cohere import ChatCohere

llm = ChatCohere(
    model="command-a-plus-05-2026",
    cohere_api_key=COHERE_API_KEY,
    temperature=0
)

PROMPT_TRIAJE = """
Eres un especialista en triaje del Service Desk para políticas internas de BimBam Buy.
Tu conocimiento proviene únicamente de los documentos internos cargados (Manual de Garantía, Política de Reembolsos y Devoluciones, Guía de Envíos, Preguntas sobre Métodos de Pago, Programa de Afiliados).

Dado el mensaje del usuario, devuelve SOLO un JSON con:
{
    "decision": "AUTO_RESOLVER" | "PEDIR_INFO" | "ABRIR_TICKET",
    "urgencia": "BAJA" | "MEDIANA" | "ALTA",
    "campos_faltantes": ["..."]
}

Reglas:
- **AUTO_RESOLVER**: Preguntas claras sobre reglas, procedimientos o definiciones que estén descritas en los documentos internos.
- **PEDIR_INFO**: Mensajes imprecisos, sin contexto o sin datos suficientes.
- **ABRIR_TICKET**: Solicitudes de excepción, autorización especial o apertura explícita de caso.

La urgencia se define por el impacto en el cliente:
- **ALTA**: producto dañado, reembolso urgente, error de despacho.
- **MEDIANA**: dudas sobre plazos, procedimientos, condiciones.
- **BAJA**: consultas generales sin impacto inmediato.
"""

from typing import Literal, List, Dict
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

class TriajeOut(BaseModel):
    decision: Literal["AUTO_RESOLVER", "PEDIR_INFO", "ABRIR_TICKET"]
    urgencia: Literal["BAJA", "MEDIANA", "ALTA"]
    campos_faltantes: List[str] = Field(default_factory=list)

chain_de_triaje = llm.with_structured_output(TriajeOut)

def triaje(mensaje: str) -> Dict:
    salida: TriajeOut = chain_de_triaje.invoke(
        [
            SystemMessage(content=PROMPT_TRIAJE),
            HumanMessage(content=mensaje)
        ]
    )
    return salida.model_dump()

from pathlib import Path
from langchain_community.document_loaders import PyMuPDFLoader

docs = []
for n in Path("docs_bimbambuy/").glob("*.pdf"):
    try:
        loader = PyMuPDFLoader(str(n))
        docs.extend(loader.load())
    except Exception as e:
        print(f"Error cargando archivo: {n.name}: {e}")

from langchain_text_splitters import RecursiveCharacterTextSplitter
splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30)
chunks = splitter.split_documents(docs)

from langchain_cohere import CohereEmbeddings
modelo_embeddings = CohereEmbeddings(
    model="embed-multilingual-v3.0",
    cohere_api_key=COHERE_API_KEY
)

from langchain_community.vectorstores import FAISS
vectorstore = FAISS.from_documents(chunks, modelo_embeddings)

retriever = vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": 0.3, "k": 3}
)

from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

prompt_rag = ChatPromptTemplate(
    [
        ("system",
            """Eres un especialista en triaje del Service Desk de la empresa BimBam Buy.
            Responde siempre en español utilizando únicamente la información contenida en los documentos internos cargados.
            Si la respuesta no está en los documentos, responde exactamente con: "No lo sé".
            """
        ),
        ("human", "Contexto: {context}\nPregunta del empleado: {input}")
    ]
)

document_chain = create_stuff_documents_chain(llm, prompt_rag)

def busqueda_de_respuestas_RAG(pregunta) -> Dict:
    documentos_relacionados = retriever.invoke(pregunta)
    if not documentos_relacionados:
        return {"respuesta": "No lo sé", "citaciones": [], "documentos_encontrados": False}

    answer = document_chain.invoke({"input": pregunta, "context": documentos_relacionados})

    if answer.rstrip(".!?") == "No lo sé":
        return {"respuesta": "No lo sé", "citaciones": [], "documentos_encontrados": False}

    return {"respuesta": answer, "citaciones": documentos_relacionados, "documentos_encontrados": True}

from typing import TypedDict, Optional

class AgentState(TypedDict, total=False):
    pregunta: str
    triaje: dict
    respuesta: Optional[str]
    citaciones: Optional[list]
    documentos_encontrados: Optional[bool]
    rag_exito: bool
    accion_final: str

def nodo_triaje(state: AgentState) -> AgentState:
    return {"triaje": triaje(state["pregunta"])}

def nodo_auto_resolver(state: AgentState) -> AgentState:
    respuesta_RAG = busqueda_de_respuestas_RAG(state["pregunta"])
    update: AgentState = {
        "respuesta": respuesta_RAG["respuesta"],
        "citaciones": respuesta_RAG["citaciones"],
        "rag_exito": respuesta_RAG["documentos_encontrados"]
    }
    update["accion_final"] = "AUTO_RESOLVER" if respuesta_RAG["documentos_encontrados"] else "PEDIR_INFO"
    return update

def nodo_pedir_info(state: AgentState) -> AgentState:
    return {"respuesta": "Necesito más informaciones sobre tu pedido.", "citaciones": [], "accion_final": "PEDIR_INFO"}

def nodo_abrir_ticket(state: AgentState) -> AgentState:
    tri = state["triaje"]
    return {"respuesta": f"Abrir ticket con urgencia {tri['urgencia']}. Pedido: {state['pregunta']}.", "citaciones": [], "accion_final": "ABRIR_TICKET"}

def arista_decision_triaje(state: AgentState) -> str:
    tri = state["triaje"]
    if tri["decision"] == "AUTO_RESOLVER":
        return "rag"
    elif tri["decision"] == "PEDIR_INFO":
        return "info"
    else:
        return "ticket"

def arista_decision_rag(state: AgentState) -> str:
    if state["rag_exito"]:
        return "ok"
    KEYWORDS_ABRIR_TICKET = ["aprobación", "aprobar", "excepción", "liberación", "autorización", "autorizar", "abrir ticket", "acceso especial"]
    if any(keyword in state["pregunta"].lower() for keyword in KEYWORDS_ABRIR_TICKET):
        return "ticket"
    return "info"

from langgraph.graph import START, END, StateGraph

workflow = StateGraph(AgentState)
workflow.add_node("triaje", nodo_triaje)
workflow.add_node("auto_resolver", nodo_auto_resolver)
workflow.add_node("pedir_info", nodo_pedir_info)
workflow.add_node("abrir_ticket", nodo_abrir_ticket)

workflow.add_edge(START, "triaje")
workflow.add_conditional_edges("triaje", arista_decision_triaje, {"rag": "auto_resolver", "info": "pedir_info", "ticket": "abrir_ticket"})
workflow.add_conditional_edges("auto_resolver", arista_decision_rag, {"info": "pedir_info", "ticket": "abrir_ticket", "ok": END})
workflow.add_edge("pedir_info", END)
workflow.add_edge("abrir_ticket", END)

grafo = workflow.compile()

def responder_usuario(pregunta: str) -> str:
    salida = grafo.invoke({"pregunta": pregunta})
    return salida["respuesta"]