from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Athlete(Base):
    __tablename__ = 'athletes'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    university = Column(String, nullable=False)
    event = Column(String, nullable=False)
    record = Column(Float, nullable=False)

    def __repr__(self):
        return f"<Athlete(name='{self.name}', university='{self.university}', event='{self.event}', record={self.record})>"

class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    date = Column(String, nullable=False)
    location = Column(String, nullable=False)

    def __repr__(self):
        return f"<Event(name='{self.name}', date='{self.date}', location='{self.location}')>"