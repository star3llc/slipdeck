from pathlib import Path
import tempfile
from typing import List
from fpdf import FPDF
from datetime import datetime
from PyPDF2 import PdfWriter, PdfReader

from slipdeck.models.order import Card, Marketplace, Order
from slipdeck.models.pull_card import PullCard
from slipdeck.utilities.price_util import get_price_as_float

NEW_LINE_HEIGHT = 0.1
PAGE_WIDTH = 4
PAGE_HEIGHT = 6
HORIZONTAL_MARGIN = 0.2
TOP_MARGIN = 0.1
BOTTOM_MARGIN = 0.2
STANDARD_FONT_SIZE = 6
ENABLE_BORDERS = 1
SHIP_TO_HEADER_FONT_SIZE = 12
ORDER_NUM_HEADER_FONT_SIZE = 10
VARIANT_TYPES = ["Foil", "Holo", "Reverse", "Rare", "Promo", "Shiny", "Full Art"]


class PullSheetPDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers = ["Qty", "Description", "Price"]
        self.col_widths = [0.4, 2.8, 0.4]
        self.col_aligns = ["C", "L", "R"]
        # Define colors for alternating rows
        self.even_row_color = (240, 240, 240)  # Light gray
        self.odd_row_color = (255, 255, 255)  # White
        self.row_count = 0  # Track row count for alternating colors

    def get_expected_row_lines(self, description):
        return NEW_LINE_HEIGHT * len(
            self.multi_cell(
                self.col_widths[1],
                NEW_LINE_HEIGHT,
                description,
                border=ENABLE_BORDERS,
                split_only=True,
            )
        )

    def print_table_headers(self):
        self.set_font("Arial", "B", STANDARD_FONT_SIZE)

        for i, header in enumerate(self.headers):
            self.cell(
                self.col_widths[i],
                NEW_LINE_HEIGHT,
                header,
                border=ENABLE_BORDERS,
                align=self.col_aligns[i],
            )
        self.ln(NEW_LINE_HEIGHT)

    def update_card_font_styles(self, card: PullCard):
        self.update_card_count(card)
        self.update_card_price(card)
        self.update_card_description(card)

    def update_card_count(self, card: PullCard):
        if card.quantity > 1:
            card.quantity_text = f"--**{card.quantity}**"
        else:
            card.quantity_text = str(card.quantity)

    def update_card_price(self, card: PullCard):
        # Convert card.price to a float since it's a string then check if it's greater than 0.49
        if float(card.price[1:]) > 0.49:
            card.price = f"--**{card.price}**--"

    def update_card_description(self, card: PullCard):
        for variant in VARIANT_TYPES:
            if variant in card.description:
                card.description = f"--**{card.description}**--"
                return

    def create_table(self, game_type: str, cards: list[PullCard]):
        self.add_page()
        self.row_count = 0
        self.set_font("Arial", "B", ORDER_NUM_HEADER_FONT_SIZE)
        self.cell(text=f"{game_type} ({len(cards)} Distinct Cards)", ln=True)
        self.ln(NEW_LINE_HEIGHT)
        self.print_table_headers()
        self.set_font("Arial", "", STANDARD_FONT_SIZE)

        for card in cards:
            self.update_card_font_styles(card)
            row_lines = self.get_expected_row_lines(card.description)

            # Set background color for the row
            if self.row_count % 2 == 0:
                self.set_fill_color(*self.even_row_color)
            else:
                self.set_fill_color(*self.odd_row_color)

            self.cell(
                self.col_widths[0],
                row_lines,
                card.quantity_text,
                border=ENABLE_BORDERS,
                align=self.col_aligns[0],
                markdown=True,
                fill=True,
            )
            self.multi_cell(
                self.col_widths[1],
                NEW_LINE_HEIGHT,
                card.description,
                border=ENABLE_BORDERS,
                new_y="TOP",
                max_line_height=NEW_LINE_HEIGHT,
                align=self.col_aligns[1],
                fill=True,
                markdown=True,
            )
            self.cell(
                self.col_widths[2],
                row_lines,
                card.price,
                border=ENABLE_BORDERS,
                align=self.col_aligns[2],
                fill=True,
                markdown=True,
            )
            self.ln(row_lines)
            self.row_count += 1  # Increment row count

        self.ln(NEW_LINE_HEIGHT)
        self.set_font("Arial", "B", STANDARD_FONT_SIZE)
        self.cell(
            self.col_widths[0] + self.col_widths[1],
            NEW_LINE_HEIGHT,
            f"Total Cards: {sum(card.quantity for card in cards)}",
            border=False,
            align="C",
        )


class OrderPDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_order = None
        self.current_order_info = {}
        self.headers = ["Qty", "Description", "Price", "Total Price"]
        self.col_widths = [0.4, 2, 0.5, 0.7]
        self.col_aligns = ["C", "L", "R", "R"]

    def header(self):
        pass

    def footer(self):
        self.set_y(-0.3)
        self.set_font("Arial", "I", STANDARD_FONT_SIZE)
        order_label = f"Order: {self.current_order}" if self.current_order else ""
        self.cell(0, 0.2, f"{order_label} - Page {self.page_no()} of {{nb}}", 0, 0, "C")

    def add_page(self, orientation="", format="", same=False, print_table_headers=True):
        # Call the parent class's add_page method
        super().add_page(orientation, format, same)
        if print_table_headers:
            self.print_table_headers()

    def start_new_order(self, order_number, order_info):
        """Reset page counting when starting a new order"""
        self.current_order = order_number
        self.current_order_info = order_info

    def print_table_headers(self):
        self.set_font("Arial", "B", STANDARD_FONT_SIZE)

        for i, header in enumerate(self.headers):
            self.cell(
                self.col_widths[i],
                NEW_LINE_HEIGHT,
                header,
                border=ENABLE_BORDERS,
                align=self.col_aligns[i],
            )
        self.ln(NEW_LINE_HEIGHT)

        # Reset font for table rows
        self.set_font("Arial", "", STANDARD_FONT_SIZE)

    def draw_full_dashed_line(self, dash_length=0.03, space_length=0.05):
        self.set_line_width(0.01)
        self.set_dash_pattern(dash_length, space_length)
        x_start = self.l_margin
        y = self.get_y()
        self.line(x_start, y, x_start + self.epw, y)
        self.set_dash_pattern()  # Reset to solid line

    def get_expected_row_lines(self, description):
        return NEW_LINE_HEIGHT * len(
            self.multi_cell(
                self.col_widths[1],
                NEW_LINE_HEIGHT,
                description,
                border=ENABLE_BORDERS,
                split_only=True,
            )
        )

    def create_cards_table(self, cards: List[Card]):
        # Omit last card since it's not popped anymore
        for card in cards:  # Process all cards except the last one
            row_lines = self.get_expected_row_lines(card.Description)

            total_price = get_price_as_float(card.Price) * float(card.Quantity)

            self.cell(
                self.col_widths[0],
                row_lines,
                card.Quantity,
                border=ENABLE_BORDERS,
                align=self.col_aligns[0],
            )
            self.multi_cell(
                self.col_widths[1],
                NEW_LINE_HEIGHT,
                card.Description,
                border=ENABLE_BORDERS,
                new_y="TOP",
                max_line_height=NEW_LINE_HEIGHT,
                align=self.col_aligns[1],
            )
            self.cell(
                self.col_widths[2],
                row_lines,
                card.Price,
                border=ENABLE_BORDERS,
                align=self.col_aligns[2],
            )
            self.cell(
                self.col_widths[3],
                row_lines,
                f"${total_price:.2f}",
                border=ENABLE_BORDERS,
                align=self.col_aligns[3],
            )
            self.ln(row_lines)

    def print_total_row(self, cards: List[Card]):
        """Calculate totals from all cards"""
        self.ln(NEW_LINE_HEIGHT)
        total_row_width = self.w - 0.4
        self.set_font("Arial", "B", STANDARD_FONT_SIZE)

        total_quantity = sum(int(card.Quantity) for card in cards)
        total_price = sum(
            get_price_as_float(card.Price) * float(card.Quantity) for card in cards
        )

        self.cell(
            total_row_width * 2 / 3,
            NEW_LINE_HEIGHT,
            f"Total Items: {total_quantity}",
        )
        self.cell(
            total_row_width * 1 / 3,
            NEW_LINE_HEIGHT,
            f"Total: ${total_price:.2f}",
        )


def resize_image_to_height(
    self, original_width, original_height, target_height_inches, dpi=300
):
    """
    Calculate dimensions to resize an image to a target height while maintaining aspect ratio

    Args:
        original_width: Original image width in pixels
        original_height: Original image height in pixels
        target_height_inches: Desired height in inches
        dpi: Dots per inch for output

    Returns:
        Tuple of (width_pixels, height_pixels, width_inches, height_inches)
    """
    # Calculate aspect ratio
    aspect_ratio = original_width / original_height

    # Calculate target width in inches
    target_width_inches = target_height_inches * aspect_ratio

    # Convert to pixels
    target_height_pixels = int(target_height_inches * dpi)
    target_width_pixels = int(target_width_inches * dpi)

    return (
        target_width_pixels,
        target_height_pixels,
        target_width_inches,
        target_height_inches,
    )


def get_proportional_image_height(image_path: str, target_width: float):
    from PIL import Image

    with Image.open(image_path) as img:
        original_width, original_height = img.size

        # Calculate aspect ratio
        aspect_ratio = original_width / original_height

        # Calculate new height based on target width while maintaining aspect ratio
        new_height = target_width / aspect_ratio

        return new_height


def print_shipping_to_header(pdf, shipping_address):
    pdf.set_font("Arial", "B", SHIP_TO_HEADER_FONT_SIZE)

    pdf.set_font("Arial", "B", SHIP_TO_HEADER_FONT_SIZE)

    pdf.cell(text=shipping_address.name, ln=True)
    pdf.cell(text=shipping_address.address_line1, ln=True)
    if shipping_address.address_line2:
        pdf.cell(text=shipping_address.address_line2, ln=True)
    pdf.cell(text=shipping_address.city_state_zip, ln=True)


def create_order_pdf(
    orders: List[Order],
    output_dir,
    company_name,
    marketplace: Marketplace,
    progress=None,
    task_id=None,
    archive_each_order_pack_slip=False,
):
    if progress is not None and task_id is not None:
        progress.update(task_id, total=len(orders))

    with tempfile.TemporaryDirectory() as tmp_dir:
        for order in orders:
            pdf = OrderPDF(orientation="P", unit="in", format=(PAGE_WIDTH, PAGE_HEIGHT))
            pdf.alias_nb_pages()
            pdf.set_auto_page_break(auto=True, margin=BOTTOM_MARGIN)
            pdf.set_margins(HORIZONTAL_MARGIN, TOP_MARGIN)
            pdf.add_page(print_table_headers=False)
            pdf.start_new_order(order.number, order.info)

            shipping_address = order.info.shipping_address
            print_shipping_to_header(pdf, shipping_address)

            pdf.ln(NEW_LINE_HEIGHT)

            pdf.draw_full_dashed_line()

            pdf.ln(NEW_LINE_HEIGHT)

            # Print order number
            pdf.set_font("Arial", "B", ORDER_NUM_HEADER_FONT_SIZE)
            pdf.cell(text=f"Order: {order.number}", ln=True)

            pdf.ln(NEW_LINE_HEIGHT / 2)

            pdf.set_font("Arial", "", STANDARD_FONT_SIZE)
            pdf.cell(
                text=f"Thank you for buying from **{company_name}** on {marketplace.value}.",
                ln=True,
                markdown=True,
            )
            pdf.ln(NEW_LINE_HEIGHT / 3)

            cards = order.info.cards

            pdf.print_table_headers()

            pdf.create_cards_table(cards)
            pdf.print_total_row(cards)

            pdf.output(f"{tmp_dir}/{order.number}.pdf")

            if progress is not None and task_id is not None:
                progress.update(task_id, advance=1)

        merge_pdfs(tmp_dir, output_dir, f"{marketplace.value}_PackingSlips")

        # Copy all pdfs to the output directory
        if archive_each_order_pack_slip:
            for pdf_file in Path(tmp_dir).glob("*.pdf"):
                pdf_file.rename(Path(output_dir) / pdf_file.name)

        progress.update(
            task_id,
            description=f":white_heavy_check_mark: [green]Merged packing slips successfully in {output_dir}!",
        )


def merge_pdfs(tmp_dir: str, output_dir: str, pdf_type="TCGPlayer_PackingSlips"):
    pdf_writer = PdfWriter()
    pdf_files = sorted(Path(tmp_dir).glob("*.pdf"))

    for pdf_file in pdf_files:
        pdf_reader = PdfReader(str(pdf_file))
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)

    merged_pdf_path = (
        Path(output_dir)
        / f"{pdf_type}_{len(pdf_files)}_Orders_{datetime.now().strftime('%m%d%Y-%H%M')}.pdf"
    )
    with open(merged_pdf_path, "wb") as f:
        pdf_writer.write(f)

    return merged_pdf_path


def create_pull_sheet(
    magic_cards: List[Card],
    pokemon_cards: List[Card],
    misc_cards: List[Card],
    output_dir,
):
    pdf = PullSheetPDF(orientation="P", unit="in", format=(PAGE_WIDTH, PAGE_HEIGHT))
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=BOTTOM_MARGIN)
    pdf.set_margins(HORIZONTAL_MARGIN, TOP_MARGIN)

    # Sort by set then name
    magic_cards.sort(key=lambda x: (x.set, x.name, x.number, x.rarity))
    pokemon_cards.sort(key=lambda x: (x.set, x.name, x.number, x.rarity))
    misc_cards.sort(key=lambda x: (x.set, x.name, x.number, x.rarity))

    pdf.create_table("Magic", magic_cards)
    pdf.create_table("Pokemon", pokemon_cards)
    pdf.create_table("MISC.", misc_cards)

    pdf.output(
        f"{output_dir}/TCGPlayer_PullList_{datetime.now().strftime('%m%d%Y-%H%M')}.pdf"
    )
