from typing import List, Optional
from enum import Enum, auto
from pydantic import BaseModel, ConfigDict


class Marketplace(str, Enum):
    EBAY = "eBay"
    TCGPLAYER = "TCG Player"
    PRICECHARTING = "PriceCharting"
    MERCARI = "Mercari"
    OTHER = "Other"


class PageInfo(BaseModel):
    page: int
    total_pages: int
    pdf_page: int


class ShippingAddress(BaseModel):
    name: str
    address_line1: str
    address_line2: Optional[str]
    city_state_zip: str
    city: str
    state: str
    zip_code: str


class Card(BaseModel):
    Quantity: str
    Description: str
    Price: Optional[str]
    Total_Price: str
    product_line: str
    set: str
    name: str
    number: str
    rarity: str
    condition: str


class SaleInformation(BaseModel):
    order_date: str
    shipping_method: str
    buyer_name: str
    seller_name: str


class OrderInfo(BaseModel):
    page_info: List[PageInfo]
    shipping_address: ShippingAddress
    cards: List[Card]
    sale_information: SaleInformation
    marketplace: Marketplace = Marketplace.TCGPLAYER


class Order(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    number: str
    info: OrderInfo
