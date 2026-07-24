from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime

class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True, nullable=False)
    user_id: int = Field(nullable=False)
    from_id: int = Field(nullable=False)
    date: datetime = Field(default_factory=datetime.now)