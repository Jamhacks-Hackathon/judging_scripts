"""
Visualization module for JAMHacks scheduler.

This module contains functions for displaying schedules in a user-friendly format.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

# Initialize rich console
console = Console()


def format_time(dt):
    """
    Format datetime object to a readable string.

    Args:
        dt (datetime): Datetime object

    Returns:
        str: Formatted time string (e.g., "10:30 AM")
    """
    return dt.strftime("%I:%M %p")  # e.g. "10:30 AM"


def display_schedule_table(schedule, stats):
    """
    Display the schedule in a pretty table format.

    Args:
        schedule (dict): Schedule dictionary
        stats (dict): Schedule statistics
    """
    # Display overall schedule information
    console.print(
        Panel.fit(
            f"[bold green]JAMHacks 9 Judging Schedule[/bold green]\n"
            f"[cyan]Date:[/cyan] {stats['start_time'].strftime('%A, %B %d, %Y')}\n"
            f"[cyan]General Judging Start:[/cyan] {format_time(stats['start_time'])}\n"
            f"[cyan]General Judging End:[/cyan] {format_time(stats['general_end_time'])}\n"
            f"[cyan]Category Judging End:[/cyan] {format_time(stats['end_time'])}\n"
            f"[cyan]Total Teams:[/cyan] {stats['total_teams']}"
        )
    )

    # Display MLH categories information
    mlh_categories = ["Best Use of MongoDB", "Best GenAI", "Best .tech"]
    console.print(
        Panel.fit(
            f"[bold yellow]MLH Categories[/bold yellow]\n"
            f"Teams with MLH categories will be prioritized for Room 6 in general judging:\n"
            f"{', '.join(mlh_categories)}"
        )
    )

    # Display general judging schedule
    console.print("\n[bold green]== GENERAL JUDGING SCHEDULE ==[/bold green]")
    for room_num, room_schedule in schedule["general"].items():
        table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
        table.add_column("Room")
        table.add_column("Team")
        table.add_column("Start Time")
        table.add_column("Categories")

        console.print(
            f"[bold cyan]Room {room_num}[/bold cyan] - [yellow]{len(room_schedule)} teams[/yellow]"
        )

        # Check if room is empty
        if not room_schedule:
            console.print("[italic]No teams assigned to this room[/italic]\n")
            continue

        # Print schedule for this room
        for slot in room_schedule:
            table.add_row(
                str(room_num),
                slot["team_name"],
                format_time(slot["start_time"]),
                ", ".join(slot["categories"]),
            )

        console.print(table)
        console.print()

    # Display category judging schedules
    console.print("\n[bold green]== CATEGORY JUDGING SCHEDULES ==[/bold green]")

    for category, category_schedule in schedule["categories"].items():
        # Skip empty categories
        if not category_schedule:
            continue

        table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
        table.add_column("Category")
        table.add_column("Team")
        table.add_column("Start Time")

        console.print(
            f"[bold cyan]{category} Category[/bold cyan] - [yellow]{len(category_schedule)} teams[/yellow]"
        )

        for slot in category_schedule:
            table.add_row(category, slot["team_name"], format_time(slot["start_time"]))

        console.print(table)
        console.print()


# Import here to avoid circular imports
