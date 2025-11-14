from sqlalchemy import Column, String, Integer
from sqlalchemy.exc import SQLAlchemyError

from persistence.db import Base, SessionLocal

class Customer(Base):
    __tablename__ = 'customer'
    id_customer = Column('id_customer', Integer, primary_key=True)
    name = Column('name',String(50))
    email = Column('email',String(50))
    phone = Column('phone',String(20))
    zip= Column('zip',String(10))

    def post_customer(self):
        session = SessionLocal()
        try:
            session.add(self)
            session.commit()
            session.refresh(self)
            return self.id_customer
        finally:
            session.close()
    def put_customer(self):
        session = SessionLocal()
        try:
            customer = session.query(Customer).filter(Customer.id_customer == self.id_customer).first()
            if customer:
                customer.name = self.name
                customer.email = self.email
                customer.phone = self.phone
                customer.zip = self.zip
                session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            print("error: \n\n\n"+str(e))
            return False
        finally:
            session.close()
    def delete_customer(self):
        session = SessionLocal()
        try:
            customer = session.query(Customer).filter(Customer.id_customer == self.id_customer).first()
            if customer:
                session.delete(customer)
                session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            print("error: \n\n\n"+str(e))
        finally:
            session.close()
def get_all_customer():
    session = SessionLocal()
    try:
        return session.query(Customer).all()
    finally:
        session.close()