from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.providers.base import ProjectProvider
from app.providers.mock import MockProvider


def get_provider(db: Session = Depends(get_db)) -> ProjectProvider:
    return MockProvider(db)
