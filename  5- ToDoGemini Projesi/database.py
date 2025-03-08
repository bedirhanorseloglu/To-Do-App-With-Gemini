# Veri tabanı ile nasıl bağlantı yapacağımızı yazacağız
# Kodları "https://fastapi.tiangolo.com/tutorial/sql-databases/#create-models"dan aldık
# Bir kere yazdık bitti. Daha burayla ilgilenmeyeceğiz

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./todoai_app.db"   # database'i projenin içerisinde oluşturmamızı sağlayacak

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()   # models klasöründe kullanacağız. En son main içerisinde uygulama çalışırken database var mı varsa çalıştır diyeceğiz