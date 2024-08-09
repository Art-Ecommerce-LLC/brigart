from sqlalchemy import Column, Integer, String, DateTime, JSON, ARRAY
from datetime import datetime
from .database import Base

class Artwork(Base):
    __tablename__ = "nc_ge1h___testimgs_copy"

    id = Column(Integer, primary_key=True)
    img_label = Column(String)
    img = Column(String)
    price = Column(String)
    created_at = Column(DateTime, default=datetime)
    updated_at = Column(DateTime, default=datetime, onupdate=datetime)

class Keys(Base):
    __tablename__ = "nc_3eh7___keys"

    id = Column(Integer, primary_key=True)
    envvar = Column(String)
    envval = Column(String)
    created_at = Column(DateTime, default=datetime)
    updated_at = Column(DateTime, default=datetime, onupdate=datetime)


class Icons(Base):
    __tablename__ = "nc_sxhc___icons"

    id = Column(Integer, primary_key=True)
    img_label = Column(String)
    img = Column(String)
    created_at = Column(DateTime, default=datetime)
    updated_at = Column(DateTime, default=datetime, onupdate=datetime)

class Cookies(Base):
    __tablename__ = "nc_qng4___sessions"

    id = Column(Integer, primary_key=True)
    sessionids = Column(String)
    cookies = Column(JSON)
    created_at = Column(DateTime, default=datetime)
    updated_at = Column(DateTime, default=datetime, onupdate=datetime)

