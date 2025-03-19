import os
from pathlib import Path
import sys
from dotenv import load_dotenv
from rich.console import Console

console = Console()

SLIPDECK_COMPANY_NAME = "SLIPDECK_COMPANY_NAME"


class Config:

    def __init__(self):
        self.config_dir = Path(__file__).parent
        self.config = {}
        if not self.load_and_validate():
            sys.exit(1)

    def load_and_validate(self) -> bool:
        """Load and validate configuration, return True if successful"""
        self.company_name = os.getenv(SLIPDECK_COMPANY_NAME)

        # If not found, try loading from .env file
        if not self.company_name:
            env_file = self.config_dir / ".env"
            if env_file.exists():
                load_dotenv(env_file)
                self.company_name = os.getenv(SLIPDECK_COMPANY_NAME)

        # Validate that we have a company name
        if not self.company_name:
            console.print(
                f"[red]Error:[/red] {SLIPDECK_COMPANY_NAME} not found in system environment or .env file"
            )
            return False

        return True

    def get_company_name(self) -> str:
        return self.company_name


config = Config()
