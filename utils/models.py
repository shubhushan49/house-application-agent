from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import create_engine
from pathlib import Path

class Base(DeclarativeBase):
    __abstract__ = True

class Apartment(Base):
    __tablename__ = "apartments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(String)
    author: Mapped[str] = mapped_column(String)
    ad_title: Mapped[str] = mapped_column(String)
    is_wg: Mapped[bool] = mapped_column(Boolean, default=False)

db_path = Path(__file__).parent.parent / "db"

db_path.mkdir(exist_ok=True)

ENGINE = create_engine(f"sqlite:///{str(db_path)}/apartments.db")