from fastapi import FastAPI , Request
from starlette.responses import RedirectResponse
from starlette import status
from .models import Base
from .database import engine  # databese bağlantı için SessionLocal kullanıyoruz
from .routers.auth import router as auth_router
from .routers.todo import router as todo_router
from fastapi.staticfiles import StaticFiles

import os


app = FastAPI()
app.include_router(auth_router)
app.include_router(todo_router)

Base.metadata.create_all(bind=engine)   # veri tabanımızı oluşturacak

# Docker'da Relative Import için
script_dir = os.path.dirname(__file__)
st_abs_file_path = os.path.join(script_dir, "static")




                                                # FrontEnd'i Bağlamak
# Ana static dosyalarımızın hepsini ana app'imize tanıtacağız
# Ve ana app'e biri girerse nereye gitmesi gerektiğini belirteceğiz
# Ama asıl işimiz templates'lerle auth.py ve todo.py'i bağlamak olacak

# static klasörünü bulması için bu kodu ekliyoruz
app.mount("/static", StaticFiles(directory=st_abs_file_path), name=st_abs_file_path)
# templates klasörünü bulması için todo ve auth klasörlerinde işlem yapacağız


# Ana sayfada neresi gözükecek onun için bir şablon oluşturacağız
# Kişi tarayıcıdan websiteme girmek istediğinde tüm bilgilerine ulaşabilmek için requst nesnesini kullandık
# Yani tarayıcı üstünden gelen tüm isteklerde request nesnesi kullanacağız
# Aynı zamanda sayfa ilk açıldığında todo'daki todo-page endpoint'i gözükecek
@app.get("/")
async def read_root(request: Request):
    return RedirectResponse(url="/todo/todo-page" , status_code=status.HTTP_302_FOUND)  # templates içindeki todo.html dosyası ilk başta gözükecek


