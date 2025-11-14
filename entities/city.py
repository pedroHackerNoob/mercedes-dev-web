from sqlalchemy import Column, Integer, String
from sqlalchemy.exc import SQLAlchemyError

from persistence.db import Base, SessionLocal

class City(Base):
    __tablename__ = 'city'
    id_city = Column('id_city', Integer, primary_key=True)  # Maps 'id' to 'city_id' column
    name = Column('name',String(60))

    def post_city(self):
        session = SessionLocal()
        try:
            session.add(self)
            session.commit()
            session.refresh(self)
            return self.id_city
        finally:
            session.close()
    def put_city(self):
        session = SessionLocal()
        try:
            city = session.query(City).filter(City.id_city == self.id_city).first()
            if city:
                city.name = self.name
                session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            print("error: \n\n\n"+str(e))
            session.rollback()
            return False

        finally:
            session.close()
    def delete_city(self):
        session = SessionLocal()
        try:
            city = session.query(City).filter(City.id_city == self.id_city).first()
            session.delete(city)
            session.commit()
            return True
        except SQLAlchemyError as e:
            print("error: \n\n\n"+str(e))
            return False
        finally:
            session.close()
def get_all_city():
    session = SessionLocal()
    try:
        return session.query(City).all()
    finally:
        session.close()
