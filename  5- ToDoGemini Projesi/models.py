# Veri tabanında tutacağımız tabloları tanımlayacağız
from .database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey


class Todo(Base): # Base'den miras adlık çünkü database'de tablo oluşturuyoruz
    __tablename__ = 'Todo'
    id = Column(Integer , primary_key=True , index=True)
    title = Column(String)
    description = Column(String)
    priority = Column(Integer)
    completed = Column(Boolean, default=False)
    user_id = Column(Integer , ForeignKey("Users.user_id"))    # ilişkiyi kurduk


class User(Base):
    __tablename__ = 'Users'
    user_id = Column(Integer , primary_key=True , index=True)
    user_firstName = Column(String)
    user_lastName = Column(String)
    user_username = Column(String , unique=True)
    user_email = Column(String , unique=True)    # unique = eşsizlik kontrolü yapıyor. Bir email bir kullanıcıya ait olmalı
    user_hashPassword = Column(String)
    user_isActive = Column(Boolean , default=True)
    user_role = Column(String)
    phone_number = Column(String)
