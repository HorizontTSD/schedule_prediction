# src/models.py

from pydantic import BaseModel


class HellowRequest(BaseModel):
    names: list[str]