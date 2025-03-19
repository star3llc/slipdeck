def get_price_as_float(price: any) -> float:
    if isinstance(price, float):
        return price
    price_str = str(price)
    return float(price_str.replace("$", "").replace(",", ""))
