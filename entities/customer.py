from sqlalchemy import Column, String, Integer

from persistence.db import Base, SessionLocal

class Customer(Base):
    __tablename__ = 'customer'
    id_customer = Column('id_customer', Integer, primary_key=True)
    name = Column('name',String(50))
    email = Column('email',String(50))
    phone = Column('phone',String(20))
    zip= Column('zip',String(10))

    def save_customer(self):
        session = SessionLocal()
        try:
            session.add(self)
            session.commit()
            session.refresh(self)
            return self.id_customer
        finally:
            session.close()

def get_all_customer():
    session = SessionLocal()
    try:
        return session.query(Customer).all()
    finally:
        session.close()