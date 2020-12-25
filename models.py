from sqlalchemy.orm import relationship
from sqlalchemy import create_engine, Column, Date, Float, Integer, String, Text, ForeignKey, Enum, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
import enum
import datetime
import os

__author__ = 'Florian Österreich'


DB_STRING = "postgresql+psycopg2" + os.getenv("DATABASE_URL")[8:] if len(os.getenv("DATABASE_URL", default=[])) > 0 else 'sqlite:///test.db'

engine = create_engine(DB_STRING)

Base = declarative_base()


def create_models():
    Base.metadata.create_all(engine)


class KeyType(enum.Enum):
    CC = "CC"
    NC = "NC"
    DIN = "DIN"
    EURO = "EURO"


class Filling(Base):
    __tablename__ = "fillings"

    id = Column(Integer, primary_key=True)

    date = Column(Date, nullable=False)

    brew_id = Column('brew_id', Integer, ForeignKey('brews.id'))
    keg_id = Column('keg_id', Integer, ForeignKey('kegs.id'))

    brew = relationship("Brew", back_populates="fillings")
    keg = relationship("Keg", back_populates="fillings")


class Brew(Base):
    __tablename__ = 'brews'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    comment = Column(Text)
    original_gravity = Column(Float)
    final_gravity = Column(Float)
    size = Column(Integer)

    fillings = relationship("Filling")


class Keg(Base):
    __tablename__ = 'kegs'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    type = Column(Enum(KeyType))
    size = Column(Integer, nullable=False)
    empty = Column(Boolean, default=True, nullable=False)
    comment = Column(Text)

    keg_comments = relationship("KegComment")
    fillings = relationship("Filling")


class KegComment(Base):
    __tablename__ = 'keg_comments'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.now, nullable=False)
    location = Column(String, nullable=False)
    comment = Column(Text, nullable=False)

    keg_id = Column("keg_id", Integer, ForeignKey('kegs.id'))
