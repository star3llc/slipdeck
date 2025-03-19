from pydantic import BaseModel


class PullCard(BaseModel):
    name: str
    description: str
    number: str
    set: str
    rarity: str
    condition: str
    price: str
    quantity: int
    quantity_text: str | None = None
    order_number: str
