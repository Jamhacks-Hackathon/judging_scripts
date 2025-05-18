"""
UI module for JAMHacks scheduler.

This module contains functions for user interface elements.
"""

from rich.console import Console

# Initialize rich console
console = Console()


def print_logo():
    """Print fancy ASCII art logo"""
    logo = """
    [bold cyan]
     ██╗ █████╗ ███╗   ███╗██╗  ██╗ █████╗  ██████╗██╗  ██╗███████╗     █████╗
     ██║██╔══██╗████╗ ████║██║  ██║██╔══██╗██╔════╝██║ ██╔╝██╔════╝    ██╔══██╗
     ██║███████║██╔████╔██║███████║███████║██║     █████╔╝ ███████╗    ╚██████║
██   ██║██╔══██║██║╚██╔╝██║██╔══██║██╔══██║██║     ██╔═██╗ ╚════██║     ╚═══██║
╚█████╔╝██║  ██║██║ ╚═╝ ██║██║  ██║██║  ██║╚██████╗██║  ██╗███████║     █████╔╝
 ╚════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝     ╚════╝
    
    [bold yellow]📅 JUDGING SCHEDULER[/bold yellow]
    [/bold cyan]
    """
    console.print(logo)
