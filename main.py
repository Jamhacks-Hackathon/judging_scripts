#!/usr/bin/env python3
"""
JAMHacks 9 Judging Schedule Generator - Main Module

This is the entry point for the JAMHacks judging scheduler.
"""

import argparse
import os
import sys
from rich.console import Console

from scheduler.data_loader import load_teams_from_csv
from scheduler.scheduler import generate_schedule
from scheduler.visualizer import display_schedule_table
from scheduler.exporter import export_schedules, generate_visualizations
from scheduler.ui import print_logo

# Initialize rich console
console = Console()


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="JAMHacks 9 Judging Schedule Generator"
    )
    parser.add_argument(
        "-i", "--input", type=str, help="Input CSV file with team data", required=True
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output directory for schedules",
        default="schedules",
    )
    parser.add_argument(
        "-s",
        "--start",
        type=str,
        help="Start time (format: YYYY-MM-DD HH:MM)",
        default="2025-05-18 10:30",
    )
    parser.add_argument(
        "-b", "--buffer", type=int, help="Buffer time in minutes", default=8
    )
    parser.add_argument(
        "-r", "--rooms", type=int, help="Number of judging rooms", default=6
    )
    parser.add_argument(
        "--visualize", action="store_true", help="Generate visualizations"
    )

    return parser.parse_args()


def main():
    """Main function to run the scheduling tool"""
    # Parse command line arguments
    args = parse_args()

    # Print logo
    print_logo()

    # Validate input file exists
    if not os.path.exists(args.input):
        console.print(
            f"[bold red]Error:[/bold red] Input file '{args.input}' not found"
        )
        sys.exit(1)

    # Load teams data
    console.print("[bold blue]Loading team data...[/bold blue]")
    teams = load_teams_from_csv(args.input)
    console.print(f"[green]✓[/green] Loaded {len(teams)} teams")

    # Generate schedule
    console.print("[bold blue]Generating schedule...[/bold blue]")
    schedule, stats = generate_schedule(
        teams, args.start, buffer_minutes=args.buffer, num_rooms=args.rooms
    )
    console.print(
        f"[green]✓[/green] Schedule generated for {stats['total_teams']} teams across {len(schedule)} rooms"
    )

    # Display schedule
    display_schedule_table(schedule, stats)

    # Save schedules
    console.print(
        f"[bold blue]Saving schedules to {args.output} directory...[/bold blue]"
    )
    csv_files = export_schedules(schedule, stats, args.output)
    console.print(f"[green]✓[/green] Saved {len(csv_files)} CSV schedule files")

    # Generate visualizations if requested
    if args.visualize:
        console.print("[bold blue]Generating visualizations...[/bold blue]")
        viz_files = generate_visualizations(schedule, stats, args.output)
        console.print(f"[green]✓[/green] Generated {len(viz_files)} visualizations")

    console.print("\n[bold green]Schedule generation complete! [/bold green]🎉")
    console.print(f"Files saved to: [cyan]{os.path.abspath(args.output)}[/cyan]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Schedule generation cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
