from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from model import run_chatbot
from auth import login_user, register_user
import traceback
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], 
    allow_headers=["*"],
    expose_headers=["*"]
)

class UserLogin(BaseModel):
    username: str
    password: str

class UserQuery(BaseModel):
    user_query: str
    username: str
    password: str

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/")
async def read_root():
    return {"message": "API is running"}

@app.post("/register")
async def register(user: UserLogin):
    if register_user(user.username, user.password):
        return {"success": True, "message": "Kayıt başarılı"}
    else:
        raise HTTPException(status_code=400, detail="Kullanıcı zaten mevcut")

@app.post("/login")
async def login(user: UserLogin):
    result = login_user(user.username, user.password)
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=400, detail=result["error"])
    
@app.post("/chat")
async def chat(data: UserQuery):
    try:
        result = login_user(data.username, data.password)
        
        if not result.get("success", False):
            raise HTTPException(status_code=401, detail="Kullanıcı doğrulanamadı")

        user_id = {
            "user_name": result["username"],
            "user_id": result["user_id"]
        }

        response = run_chatbot(data.user_query, user_id)
        print(f"Chatbot Response: {response}")
        
        return {"response": response}

    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Hata Detayı: {error_details}")
        raise HTTPException(status_code=500, detail=f"Sunucu hatası: {str(e)}")





