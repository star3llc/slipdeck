"""Command line interface for Slipdeck."""

import typer
from rich.console import Console

from typing_extensions import Annotated
from typing import Optional
import sys
from slipdeck.config.config_manager import config

from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)

from slipdeck.models.order import Marketplace
from slipdeck.models.pull_card import PullCard
from slipdeck.pdf_creator import create_order_pdf, create_pull_sheet
from slipdeck.pdf_processor import parse_packing_slips
import os

# Import your logic modules here
# from .core import your_logic_function

app = typer.Typer(help="Slipdeck CLI tool")
console = Console()


@app.command(
    "pack", help="Create thermal printer friendly packing slips from TCG Player orders."
)
def pack(
    input_file: str,
    output_file_dir: Annotated[
        str,
        typer.Option("-o", "--output-dir", help="Output directory for packing slips"),
    ] = "./output",
    company_name: str = None,
    no_packing_slip: Annotated[
        bool,
        typer.Option("-npack", "--no-packing-slip", help="Don't create packing slips"),
    ] = False,
    no_pull_sheet: Annotated[
        bool,
        typer.Option(
            "-npull", "--no-pull-sheet", help="Don't create a sorted pull sheet"
        ),
    ] = False,
):
    """
    Create thermal printer friendly packing slips from TCG Player orders.

    Args:
        input_file: Path to the input CSV file containing TCG Player orders.
    """
    # Check if output directory exists, create it if it doesn't
    if not os.path.exists(output_file_dir):
        console.print(
            f"[yellow]Output directory '{output_file_dir}' doesn't exist. Creating it..."
        )
        os.makedirs(output_file_dir)
        console.print(f"[green]Created output directory: {output_file_dir}")

    company_name = company_name or config.get_company_name()
    marketplace = Marketplace.TCGPLAYER

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=Console(),  # Create a console instance
        transient=True,  # Keep progress bars visible after completion
    ) as progress:
        # Check that input path is a pdf file
        if not input_file.endswith(".pdf"):
            progress.console.print("[red]Error: Input file must be a PDF.")
            raise typer.Exit(code=1)

        # Create tasks for different operations
        parse_task = progress.add_task("[cyan]Parsing PDF and processing orders...")
        pdf_task = progress.add_task("[cyan]Creating PDFs...")

        progress.console.print(
            f"[blue]Packing slips will be generated from {input_file}"
        )

        orders = parse_packing_slips(input_file, marketplace, progress, parse_task)

        if not no_packing_slip:
            create_order_pdf(
                orders,
                output_file_dir,
                company_name,
                marketplace,
                progress,
                pdf_task,
            )

        if not no_pull_sheet:
            magic_cards: list[PullCard] = []
            magic_card_dict = {}
            pokemon_cards: list[PullCard] = []
            pokemon_card_dict = {}
            misc_cards: list[PullCard] = []
            misc_card_dict = {}

            for order in orders:
                for card in order.info.cards:
                    card_name = f"{card.set} {card.name} {card.number}"
                    if card.product_line == "Magic":
                        if card_name in magic_card_dict:
                            # Get existing card and update quantity and order info
                            existing_card: PullCard = magic_card_dict[card_name]
                            # existing_card.quantity += int(card["Quantity"])
                            # existing_card.order_number += f", {order_number}"
                            existing_card.quantity += int(card.Quantity)
                            existing_card.order_number += f", {order.number}"
                        else:
                            new_card: PullCard = PullCard(
                                name=card_name,
                                description=card.Description,
                                number=card.number,
                                set=card.set,
                                rarity=card.rarity,
                                condition=card.condition,
                                price=card.Price,
                                quantity=card.Quantity,
                                order_number=order.number,
                            )
                            magic_card_dict[card_name] = new_card
                            magic_cards.append(new_card)
                    elif card.product_line.startswith("Pokemon"):
                        if card_name in pokemon_card_dict:
                            # Get existing card and update quantity and order info
                            existing_card = pokemon_card_dict[card_name]
                            existing_card.quantity += int(card.Quantity)
                            existing_card.order_number += f", {order.number}"
                        else:
                            new_card: PullCard = PullCard(
                                name=card_name,
                                description=card.Description,
                                number=card.number,
                                set=card.set,
                                rarity=card.rarity,
                                condition=card.condition,
                                price=card.Price,
                                quantity=card.Quantity,
                                order_number=order.number,
                            )
                            pokemon_card_dict[card_name] = new_card
                            pokemon_cards.append(new_card)
                    else:
                        if card_name in misc_card_dict:
                            # Get existing card and update quantity and order info
                            existing_card = misc_card_dict[card_name]
                            existing_card.quantity += int(card.Quantity)
                            existing_card.order_number += f", {order.number}"
                        else:
                            new_card: PullCard = PullCard(
                                name=card_name,
                                description=card.Description,
                                number=card.number,
                                set=card.set,
                                rarity=card.rarity,
                                condition=card.condition,
                                price=card.Price,
                                quantity=card.Quantity,
                                order_number=order.number,
                            )
                            misc_card_dict[card_name] = new_card
                            misc_cards.append(new_card)

            # Sort the cards by name
            create_pull_sheet(
                magic_cards,
                pokemon_cards,
                misc_cards,
                output_file_dir,
            )


if __name__ == "__main__":
    app()
