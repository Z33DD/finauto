from datetime import date
from enum import Enum
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from finauto.sheets import append_transaction, fetch_categories


app = FastAPI()


class ExpernseTypeEnum(str, Enum):
    credit = "Credit"
    debit = "Debit"


class Transaction(BaseModel):
    name: str
    category: str
    expense_type: ExpernseTypeEnum
    date: date
    description: str | None = None
    price: float
    shared: bool = False


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/item/")
async def create_item(transaction: Transaction):
    categories = fetch_categories()
    if transaction.category not in categories:
        raise HTTPException(
            detail=f"Invalid category: {transaction.category}.", status_code=400
        )
    if not transaction.date:
        transaction.date = date.today()
    append_transaction(
        name=transaction.name,
        category=transaction.category,
        expense_type=transaction.expense_type,
        date=transaction.date,
        description=transaction.description,
        price=transaction.price,
    )
    return transaction
