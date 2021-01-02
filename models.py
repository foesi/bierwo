from sqlalchemy.orm import relationship
from sqlalchemy import create_engine, Column, Date, Float, Integer, String, Text, ForeignKey, Enum, DateTime, Boolean, \
    LargeBinary
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


class KegType(enum.Enum):
    CC = "CC"
    NC = "NC"
    DIN = "DIN"
    EURO = "EURO"
    HOLZ = "HOLZ"


class KegFitting(enum.Enum):
    KORB = "Korb"
    FLACH = "Flach"


class Filling(Base):
    __tablename__ = "fillings"

    id = Column(Integer, primary_key=True)

    date = Column(Date, nullable=False)

    empty_date = Column(Date)

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
    recipe = Column(String)
    protocol = Column(LargeBinary)
    size = Column(Integer)

    brew_comments = relationship("BrewComment")
    fillings = relationship("Filling")


class BrewComment(Base):
    __tablename__ = 'brew_comments'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.now, nullable=False)
    comment = Column(Text, nullable=False)

    brew_id = Column("brew_id", Integer, ForeignKey('brews.id'), nullable=False)


class Keg(Base):
    __tablename__ = 'kegs'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    type = Column(Enum(KegType))
    fitting = Column(Enum(KegFitting))
    size = Column(Integer, nullable=False)
    clean = Column(Boolean, default=False, nullable=False)
    deprecated = Column(Boolean, default=False, nullable=False)
    reserved = Column(Boolean, default=False, nullable=False)
    isolated = Column(Boolean, default=False, nullable=False)
    photo = Column(LargeBinary)
    comment = Column(Text)

    keg_comments = relationship("KegComment")
    fillings = relationship("Filling")


class KegComment(Base):
    __tablename__ = 'keg_comments'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.now, nullable=False)
    location = Column(String, nullable=False)
    comment = Column(Text, nullable=False)

    keg_id = Column("keg_id", Integer, ForeignKey('kegs.id'), nullable=False)
