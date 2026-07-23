from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from challenge_oci import responder_usuario

app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # puedes restringir si quieres
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ruta principal para frontend
@app.get("/")
def read_index():
    return FileResponse("index.html")

# Servir archivos estáticos (CSS, JS)
app.mount("/static", StaticFiles(directory="."), name="static")

# Modelo de entrada
class Pregunta(BaseModel):
    texto: str

# Endpoint del backend
@app.post("/preguntar")
def preguntar(p: Pregunta):
    respuesta = responder_usuario(p.texto)
    return {"respuesta": respuesta}
