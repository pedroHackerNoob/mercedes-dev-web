from sqlalchemy import Column, Integer, String
from persistence.db import Base, SessionLocal

class City(Base):
    __tablename__ = 'city'
    id_city = Column('id_city', Integer, primary_key=True)  # Maps 'id' to 'city_id' column
    name = Column('name',String(60))

def get_all():
    session = SessionLocal()
    try:
        return session.query(City).all()
    finally:
        session.close()