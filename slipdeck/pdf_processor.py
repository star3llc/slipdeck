import re
from typing import List
import pdfplumber

from slipdeck.models.order import (
    Card,
    Marketplace,
    Order,
    OrderInfo,
    PageInfo,
    SaleInformation,
)


def debug_print(text: str, progress=None):
    if progress is not None:
        progress.console.print(text)
    else:
        print(text)


def extract_ship_to(text: str) -> dict:
    ship_to_match = re.search(r"ShipTo:(.*?)Order Number", text, re.DOTALL)
    if ship_to_match:
        ship_to_text = ship_to_match.group(1).strip()
        lines = ship_to_text.splitlines()

        if len(lines) < 3:
            # ERROR: Not enough lines in the shipping address
            return {}

        name = lines[0].strip()
        city_state_zip = lines[-1].strip()
        address_lines = lines[1:-1]

        city_state_zip_parts = city_state_zip.split(",")
        if len(city_state_zip_parts) != 2:
            return {}

        city = city_state_zip_parts[0].strip()
        state_zip_parts = city_state_zip_parts[1].strip().split(" ")
        if len(state_zip_parts) != 2:
            return {}

        state = state_zip_parts[0].strip()
        zip_code = state_zip_parts[1].strip()

        shipping_address = {
            "name": name,
            "address_line1": address_lines[0],
            "address_line2": address_lines[1] if len(address_lines) > 1 else "",
            "city_state_zip": f"{city}, {state} {zip_code}",
            "city": city,
            "state": state,
            "zip_code": zip_code,
        }

        return shipping_address
    return {}


def extract_cards_old(page: pdfplumber.page.Page) -> list:
    cards = []
    table_settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "intersection_tolerance": 5,
        "text_x_tolerance": 2,
        "text_y_tolerance": 2,
    }

    table = page.extract_table(table_settings)
    if table:
        header = table[0]
        for row in table[1:]:
            row_data = dict(zip(header, row))
            cards.append(row_data)

    # Process each card's description
    for card in cards:
        description = card.get("Description", "")
        card_info_tokens = description.split("-")
        if len(card_info_tokens) < 6:
            # ERROR: Not enough information in the card description
            continue

        card_info = {
            "product_line": card_info_tokens[0].strip(),
            "set": card_info_tokens[1].strip(),
            "name": card_info_tokens[2].strip(),
            "number": card_info_tokens[3].strip(),
            "rarity": card_info_tokens[4].strip(),
            "condition": card_info_tokens[5].strip(),
        }
        card.update(card_info)

    return cards


def row_to_card(row_data: dict) -> Card:
    description = row_data["Description"]
    description = row_data.get("Description", "")
    card_info_tokens = description.split("-")
    card_info = {
        "product_line": card_info_tokens[0].strip(),
        "set": card_info_tokens[1].strip(),
        "name": card_info_tokens[2].strip(),
        "number": card_info_tokens[3].strip(),
        "rarity": card_info_tokens[4].strip(),
        "condition": card_info_tokens[5].strip(),
    }
    return Card(
        Quantity=row_data["Quantity"],
        Description=row_data["Description"],
        Price=row_data["Price"],
        Total_Price=row_data["Total Price"],
        **card_info,
    )


def extract_cards(page: pdfplumber.page.Page) -> List[Card]:
    cards = []
    table_settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "intersection_tolerance": 5,
        "text_x_tolerance": 2,
        "text_y_tolerance": 2,
    }

    table = page.extract_table(table_settings)
    if table:
        header = table[0]
        for row in table[1:]:
            row_data = dict(zip(header, row))
            if row_data["Price"]:
                cards.append(row_to_card(row_data))

    return cards


def parse_packing_slips(
    pdf_path: str, marketplace: Marketplace, progress=None, task_id=None
) -> List[Order]:
    orders: List[Order] = []
    order_info_pattern = re.compile(
        r"OrderNumber:(?P<order_number>\S+)\s+Page(?P<page>\d+)of(?P<total>\d+)"
    )
    with pdfplumber.open(pdf_path) as pdf:
        # Update the total progress with the number of pages
        if progress is not None and task_id is not None:
            progress.update(task_id, total=len(pdf.pages))
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()

            # Extract order information
            order_info_match = order_info_pattern.search(text)
            if order_info_match:
                order_number = order_info_match.group("order_number")
                page_info_item = PageInfo(
                    page=int(order_info_match.group("page")),
                    total_pages=int(order_info_match.group("total")),
                    pdf_page=i + 1,
                )
                ship_to_data = extract_ship_to(text)
                cards = extract_cards(page)

                existing_order = next(
                    (order for order in orders if order.number == order_number),
                    None,
                )

                if existing_order:
                    order_info = existing_order.info
                    order_info.cards.extend(cards)

                    if not order_info.shipping_address and ship_to_data:
                        order_info.shipping_address = ship_to_data
                    existing_order.info.page_info.append(page_info_item)
                else:
                    # First page of order
                    sale_information = extract_sale_information(page)

                    orders.append(
                        Order(
                            number=order_number,
                            info=OrderInfo(
                                page_info=[page_info_item],
                                shipping_address=ship_to_data,
                                cards=cards,
                                sale_information=sale_information,
                                marketplace=marketplace,
                            ),
                        )
                    )

            if progress is not None and task_id is not None:
                progress.update(task_id, advance=1)

        progress.update(
            task_id,
            description=f"[green]:white_heavy_check_mark: Processed {len(orders)} orders!",
        )
        return orders


def extract_sale_information(page: pdfplumber.page.Page) -> SaleInformation:
    """
    Extracts text from the shipping details box by cropping a region from the page.

    Adjust the bbox coordinates to match the location of your box.
    Bbox is in the form (x0, y0, x1, y1)
    """
    bbox = (280, 194, 580, 282)
    box = page.within_bbox(bbox)
    box_text = box.extract_text(x_tolerance=1, y_tolerance=1)

    pattern = re.compile(
        r"Order Date:\s*(?P<order_date>.+?)\s*\n"
        r"Shipping Method:\s*(?P<shipping_method>.+?)\s*\n"
        r"Buyer Name:\s*(?P<buyer_name>.+?)\s*\n"
        r"Seller Name:\s*(?P<seller_name>.+)",
        re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(box_text)
    if match:
        return SaleInformation(**match.groupdict())
    else:
        raise ValueError("Failed to extract sale information from the page.")
