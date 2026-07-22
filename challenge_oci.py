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