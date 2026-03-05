from pydantic import BaseModel
from typing import List

class LineItem(BaseModel):
    description: str
    quantity: int
    unit_price: float

class InvoiceData(BaseModel):
    vendor: str
    date: str
    items: List[LineItem]
    extracted_total: float
