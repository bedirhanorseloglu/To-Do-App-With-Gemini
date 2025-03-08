from fastapi import APIRouter , Depends , HTTPException , Request
from jose.constants import ALGORITHMS
from pydantic import BaseModel
from ..models import User
from passlib.context import CryptContext    # parola hashleyerek şifrelemek için kullanılır
from sqlalchemy.orm import Session
from ..database import SessionLocal
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm , OAuth2PasswordBearer   # token endpoint'inde kullandık
from jose import jwt , JWTError    # token oluşturmak için kullanılır
from datetime import timedelta , datetime , timezone

# Frontend'i Bağlamak2
from fastapi .templating import Jinja2Templates    # {% %} syntax'i Jinja olarak geçer.



router = APIRouter(
    prefix="/auth", # prefix ile buradaki tüm endpointlerin başına "/auth" eklenecek
    tags=["Authentication"]   # swagger ui'da burada oluşturulan endpointlerin başuna "Authentication" yazılacak
)


# Frontend'i bağlamak2
templates = Jinja2Templates(directory="app/templates")


# Tokenda gireceğimiz bilgileri yazacağız
SECRET_KEY = "ai27qwjph7uvxwpocwmz3qo723gecwtifvllz0it11spse991r3s6agyi2368llq" # random olarak oluşturduk "https://www.random.org/strings/"
ALGORITHMS = "HS256"    #şifreleme algoritması





# Veri tabanı bağlantısını yapacağız
# Yazacağımz tüm endpointler artık buraya "DEPEND" edecek. Yani bağımlı olacak
def get_db():
    db = SessionLocal()
    try:
        yield db    # yiled, return gibi düşünülebilir. Farkı yield kullanılan fonks. genereted denir. Return bir değer döndürürken yield birden fazla değer döndürebilir.
    finally:
        db.close()

db_dependency = Annotated[Session , Depends(get_db)]



bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")    # hash'lemek için kullanılacak
oauth_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")


# Post için request sınıfı oluşturalım
class CreateUserRequset(BaseModel):
    user_firstName: str
    user_lastName: str
    user_username: str
    user_email: str
    user_hashPassword: str
    user_isActive: bool
    user_role: str
    phone_number: str


    model_config = {
        "json_schema_extra": {
            "example": {
                "user_firstName": "John",
                "user_lastName": "Doe",
                "user_username": "johndoe",
                "user_email": "johndoe@example.com",
                "user_hashPassword": "password123",
                "user_isActive": True,
                "user_role": "user"
            }
        }
    }




# "/token" endpoint'inde basemodel olarak kullandık. Daha yapısal olması için
class Token(BaseModel):
    access_token: str
    token_type: str






@router.post("/create_user" , status_code=201)
async def create_user(db: db_dependency , create_user_request: CreateUserRequset):
    # user = User(**create_user_request.dict())     normalde bunu kullanıyorduk ancak password'u biz hashlemek istiyoruz. Bu yüzden bunu kullanmayacağız
    # O yüzden bu şekilde uzun halini kullanacağız
    user = User(
        user_firstName = create_user_request.user_firstName,
        user_lastName = create_user_request.user_lastName,
        user_username = create_user_request.user_username,
        user_email = create_user_request.user_email,
        user_hashPassword = bcrypt_context.hash(create_user_request.user_hashPassword), # parola'yı hashledik
        user_isActive = create_user_request.user_isActive,
        user_role = create_user_request.user_role,
        phone_number = create_user_request.phone_number
    )

    db.add(user)
    db.commit()





# Şifreyi hash'ledik. Peki kullanıcının girdiği parola ile hash'lenmiş parola eşleşiyor mu kontrolünü nasıl yapacağız?
def authenticate_user(username: str , password: str , db):
    user = db.query(User).filter(User.user_username == username).first()
    if not user:
        return False

    if not bcrypt_context.verify(password , user.user_hashPassword):
        return False

    return user







# JWT ENCODING
# JWT Token'ını oluşturacak fonksiyonu yazalım
def create_access_token(username: str , user_id: int , role: str , expires_delta: timedelta):
    encode = {
        "sub": username,
        "id": user_id,
        "role": role
    }

    expires = datetime.now(timezone.utc) + expires_delta    # "şu anki zaman + expires_delta" kadar süre geçtikten sonra token geçersiz olacak
    encode.update({"exp": expires})     # encpde dict'imize "exp" key'ini ekleyip expires değerini atadık ve token'ın geçerlilik süresini belirledik

    return jwt.encode(encode , SECRET_KEY , algorithm=ALGORITHMS)





# Oluşturduğumuz "authenticate_user" fonksiyonunu kullanarak kullanıcının giriş yapıp yapmadığını kontrol edelim
# Token, kullanıcı giriş yaptığında kullanıcıya verdiğimiş şifrelenmş bir string...
# ... Kullanıcı yapacağı tüm isteklerde bu token'ı kullanacak.
@router.post("/token" , response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm , Depends()], db: db_dependency):
    user = authenticate_user(form_data.username , form_data.password , db)
    if not user:
        raise HTTPException(status_code=401 , detail="Kullanıcı doğrulanamadı.")

    # kullanıcı varsa token oluşturacağız
    token = create_access_token(user.user_username , user.user_id , user.user_role , timedelta(minutes=60))  # token oluşturabiliriz artık
    return{"access_token": token , "token_type": "bearer"}







# JWT DECODING
# İçine gireceğimiz token'la birlikte gerçekten böyle bir kullanıcı var mı kontrolünü yapacağız
# Bu fonksiyonu todo.py'de dependecy olarak vereceğiz ki atılan isteklerin gerçekten bizim kullanıcukanıcımızın istekleri mi olduğunu kontrol edebilelim
async def get_current_user(token: Annotated[str, Depends(oauth_bearer)]):
    try:
        payload = jwt.decode(token , SECRET_KEY , algorithms=[ALGORITHMS])
        username = payload.get('sub')
        user_id = payload.get('id')
        user_role = payload.get('role')

        if username is None or user_id is None:
            raise HTTPException(status_code=401 , detail="Kullanıcı doğrulanamadı.")

        return {"username": username , "id": user_id , "user_role": user_role}

    except JWTError:
        raise HTTPException(status_code=401 , detail="Token geçersiz.")




# Frontrend'i bağlamak 2
# Login sayfası oluşturacağız
# Bu sayfada kullanıcının kayıt olmasını sağlayacağız
@router.get("/login-page" , status_code=201)
def render_login_page(request: Request):
    return templates.TemplateResponse("login.html" , {"request": request})

# Register sayfası oluşturacağız
# Bu sayfada kullanıcının kayıt olmasını sağlayacağız
@router.get("/register-page" , status_code=201)
def render_register_page(request: Request):
    return templates.TemplateResponse("register.html" , {"request": request})