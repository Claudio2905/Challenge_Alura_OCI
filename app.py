from fastapi import FastAPI
from pydantic import BaseModel
from challenge_oci import responder_usuario  # importa tu función desde tu archivo principal

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # puedes restringir a ["http://127.0.0.1:5500"] si quieres
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Pregunta(BaseModel):
    texto: str

@app.post("/preguntar")
def preguntar(p: Pregunta):
    respuesta = responder_usuario(p.texto)
    return {"respuesta": respuesta}
