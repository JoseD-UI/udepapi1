from fastapi import FastAPI, File, UploadFile
import os
import requests
from datetime import datetime, timedelta

app = FastAPI()

UPLOAD_FOLDER = "./uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configuración de autenticación
URL_TOKEN = "https://pagos.udep.edu.pe:5000/api/v1/oauth/token"
CLIENT_ID = "AppTerceroAuthApp"
CLIENT_SECRET = "FwQK11gMqQyRSO//AMkGefHejJvQw/SAHCub0Rh5sHU="
USERNAME = "jose.diaz"
PASSWORD = "ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f"

# Palabras clave y tiempo de filtrado
PALABRAS_CLAVE = ["SL", "124", "WE", "CREP"]
HORAS_LIMITE = 16

def obtener_token():
    payload = {
        "grant_type": "password",
        "username": USERNAME,
        "password": PASSWORD,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(URL_TOKEN, data=payload, headers=headers)

    if response.status_code == 200:
        token = response.json().get("access_token")
        print("✅ Token obtenido:", token)
        return token
    else:
        print("❌ Error al obtener el token:", response.text)
        return None

def filtrar_archivo(file_path):
    file_name = os.path.basename(file_path)
    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
    fecha_limite = datetime.now() - timedelta(hours=HORAS_LIMITE)
    
    if any(palabra in file_name.upper() for palabra in PALABRAS_CLAVE) and mod_time >= fecha_limite:
        print(f"✅ Archivo {file_name} cumple con los criterios de filtrado.")
        return True
    else:
        print(f"❌ Archivo {file_name} NO cumple con los criterios de filtrado.")
        return False

def validar_archivo(token, file_path):
    headers = {"Authorization": f"Bearer {token}"}
    
    with open(file_path, "rb") as file:
        files = {"file": file}
        response = requests.post("https://pagos.udep.edu.pe:5000/api/v1/icb/UploadFileTXTBcoICB/1", headers=headers, files=files)

    if response.status_code == 200:
        print(f"✅ Archivo {file_path} validado correctamente.")
        return response.json()
    else:
        print(f"❌ Error al validar {file_path}: {response.text}")
        return None

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_location = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(file_location, "wb") as buffer:
            buffer.write(await file.read())
        
        if not filtrar_archivo(file_location):
            os.remove(file_location)  # Eliminar archivo si no cumple
            return {"filename": file.filename, "status": "Rechazado - No cumple con los criterios"}
        
        token = obtener_token()
        if token:
            response = validar_archivo(token, file_location)
        
        return {"filename": file.filename, "status": "Archivo recibido y validado"}
    except Exception as e:
        print(f"❌ Error en el procesamiento del archivo: {str(e)}")
        return {"error": f"Error al procesar el archivo: {str(e)}"}
