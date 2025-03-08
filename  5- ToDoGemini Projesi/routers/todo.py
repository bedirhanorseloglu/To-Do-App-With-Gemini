from fastapi import APIRouter , Depends , Path , HTTPException , Request
from pydantic import BaseModel , Field
from sqlalchemy.orm import Session
from ..models import Base , Todo
from ..database import engine , SessionLocal # databese bağlantı için SessionLocal kullanıyoruz
from typing import Annotated
from ..routers.auth import get_current_user   # jwt decoing'i dependency olarak vereceğiz

# Frontend'i bağlamak 3
from fastapi.templating import Jinja2Templates    # {% %} syntax'i Jinja olarak geçer.

from starlette.responses import RedirectResponse
from starlette import status

# Gemini için
from dotenv import load_dotenv
import google.generativeai as genai
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, HumanMessage

# AI sonucunu text formatında göstermek için
import markdown
from bs4 import BeautifulSoup





router = APIRouter(
    prefix="/todo", # prefix ile buradaki tüm endpointlerin başına "/todo" eklenecek
    tags=["Todo"],  # swagger ui'da burada oluşturulan endpointlerin başuna "Todo" yazılacak
)



# Frontend'i bağlamak 3
templates = Jinja2Templates(directory="app/templates")





# POST işlemi için Request Sınıfı
class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=1000)
    priority: int = Field(gt=0 , lt=6)
    completed: bool

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Örnek Başlık",
                "description": "Örnek Açıklama",
                "priority": 1,
                "completed": False
            }
        }
    }




# Veri tabanı bağlantısını yapacağız
# Yazacağımz tüm endpointler artık buraya "DEPEND" edecek. Yani bağımlı olacak
def get_db():
    db = SessionLocal()
    try:
        yield db    # yiled, return gibi düşünülebilir. Farkı yield kullanılan fonks. genereted denir. Return bir değer döndürürken yield birden fazla değer döndürebilir.
    finally:
        db.close()



db_dependency = Annotated[Session , Depends(get_db)]
user_dependecy = Annotated[dict , Depends(get_current_user)]  # şimdi bu bağımlılığı CRUD fonksiyonlarımıza ekleyeceğiz




@router.get("/")
async def read_all(user: user_dependecy , db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401 , detail="Kullanıcı doğrulanamdı")

    # return db.query(Todo).all() # şu an "all" olarak hepsini getiriyoruz. İleride ise sadce o kullanıcının todo'larını getirebiliriz artık
    return db.query(Todo).filter(Todo.user_id == user.get('id')).all()




# ID'ye göre bir filtreleme işlemi yapalım
@router.get("/todo/{id}" , status_code=200)
async def get_by_id(user: user_dependecy , db: db_dependency , id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401 , detail="Kullanıcı doğrulanamdı")

    todo = db.query(Todo).filter(Todo.id == id).filter(Todo.user_id == user.get('id')).first()
    # buradakı bu user.get('id') kısmı auth.py'de get_current_user fonksiyonunda token'dan gelen user'ın id'si

    if todo is not None:
        return todo
    raise HTTPException(status_code=404 , detail="Todo bulunamadı")



# POST işlemine geçeceğiz
@router.post("/todo", status_code=201)
async def create_todo(user: user_dependecy , db: db_dependency , todo_request: TodoRequest):
    if user is None:
        raise HTTPException(status_code=401 , detail="Kullanıcı doğrulanamdı")

    todo = Todo(**todo_request.dict() , user_id = user.get("id"))
    todo.description = create_todo_with_gemini(todo.description)
    db.add(todo)
    db.commit()
    return {"message": "Todo başarıyla oluşturuldu"}


# UPDATE işlemi
@router.put("/todo/{todo_id}", status_code=200)
async def update_todo(user: user_dependecy,db: db_dependency, todo_request: TodoRequest, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.user_id == user.get('id')).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo bulunamadı")

    todo.title = todo_request.title
    todo.description = todo_request.description
    todo.priority = todo_request.priority
    todo.completed = todo_request.completed

    db.add(todo)
    db.commit()
    return {"message": "Todo başarıyla güncellendi"}


# DELETE işlemi
@router.delete("/todo/{id}" , status_code=204)
async def delete_todo(user: user_dependecy , db: db_dependency , id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401 , detail="Kullanıcı doğrulanamdı")

    todo = db.query(Todo).filter(Todo.id == id).filter(Todo.user_id == user.get('id')).first()
    if todo is None:
        raise HTTPException(status_code=404 , detail="Todo bulunamadı")

    db.delete(todo)
    db.commit()
    return {"message": "Todo başarıyla silindi"}




# Frontend'i bağlamak 3
# Kullanıcı kayıtlı değilse login sayfasına yönlendireceğiz sürekli. Bunun için bir fonksiyon yazalım
def rediirect_login():
    redirect_response = RedirectResponse(url="/auth/login-page" , status_code=302)
    redirect_response.delete_cookie("access_token")
    return redirect_response



@router.get("/todo-page")
async def render_todo_page(request: Request , db: db_dependency):
    # Burada direkt şu şeklilde yazmayacağız. Çünkü bu şekilde yazarsak kullanıcı login yapmadan da todo ekleyebilir.
    # Dolayısıyla kullanıcı kayıtlı değilse bu sayfaya erişmemeli
    # return templates.TemplateResponse("todo.html" , {"request": request})
    try:
        user = await get_current_user(request.cookies.get("access_token"))
        if user is None:
            return rediirect_login()

        todos = db.query(Todo).filter(Todo.user_id == user.get('id')).all()
        return templates.TemplateResponse("todo.html" , {"request": request , "todos": todos , "user": user})

    except:
        return rediirect_login()






# Add To Do Sayfası
@router.get("/add-todo-page")
async def render_add_todo_page(request: Request):
    try:
        user = await get_current_user(request.cookies.get("access_token"))
        if user is None:
            return rediirect_login()


        return templates.TemplateResponse("add-todo.html" , {"request": request , "user": user})

    except:
        return rediirect_login()




# Edit To Do Sayfası
@router.get("/edit-todo-page/{todo_id}")
async def render_todo_page(request: Request , todo_id: int , db: db_dependency):
    try:
        user = await get_current_user(request.cookies.get("access_token"))
        if user is None:
            return rediirect_login()

        todo = db.query(Todo).filter(Todo.id == todo_id).first()
        return templates.TemplateResponse("edit-todo.html" , {"request": request , "todo": todo , "user": user})

    except:
        return rediirect_login()




# GEMINI'yı kullanmak için bir fornksiyon yazalım
def create_todo_with_gemini(todo_stirng: str):
    # İlk olarak .env'deki gemini api'mizi alıp Langchain Framework'üne biz bu LLM'i kullancağız diyeceğiz
    load_dotenv() # yukarıda eklediğimiz kütüphane ve bu fonksiyonla .env dosyasını okuyacağız
    genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")
    response = llm.invoke(
        [
            # Gemini'ya yapmasını istediğimiz şeyi ve şu anda yazan descripyon'ı gönderiyoruz.
            HumanMessage(content="Yapılacaklar listeme eklemeniz için size bir yapılacaklar maddesi vereceğim. Yapmanızı istediğim şey, bu yapılacaklar için daha uzun ve kapsamlı bir açıklama oluşturmak. Bir sonraki mesajım benim yapılacaklarım olacak:"),
            HumanMessage(content=todo_stirng),
        ]
    )
    return markdown_to_text(response.content)


# AI ile oluşturduğumuz yazılar markdown şeklinde oluşturuluyordu. Bunu text olarak düzeltmek için bir fonksiyon yazalım
# Bu fonksiyonu bu şekilde her yerde kullanabiliriz.
def markdown_to_text(markdown_string: str):
    html = markdown.markdown(markdown_string)
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()
    return text




