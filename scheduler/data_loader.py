"""
Data loading module for JAMHacks scheduler.

This module contains functions for loading team data from CSV files.
"""

import pandas as pd
import sys
from rich.console import Console

# Initialize rich console
console = Console()


def load_teams_from_csv(file_path):
    """
    Load teams from a CSV file.

    Args:
            file_path (str): Path to the CSV file

    Returns:
            list: A list of team dictionaries

    Raises:
            SystemExit: If the file cannot be loaded or has invalid format
    """
    try:
        # Load CSV file
        df = pd.read_csv(file_path)

        # Basic validation - check required columns
        required_columns = ["BUIDL ID", "BUIDL name", "Track", "Bounties"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            console.print(
                f"[bold red]Error:[/bold red] Missing required columns: {', '.join(missing_columns)}"
            )
            console.print(f"CSV file must contain: {', '.join(required_columns)}")
            sys.exit(1)

        # Process the dataframe to extract team names and categories
        teams = []
        for _, row in df.iterrows():
            team_name = row["BUIDL name"]

            # Skip rows with missing team names
            if pd.isna(team_name):
                continue

            # Parse categories from Track and Bounties columns
            categories = []

            if not pd.isna(row["Track"]):
                tracks = row["Track"].split(",")
                categories.extend([t.strip() for t in tracks])

            if not pd.isna(row["Bounties"]):
                bounties = row["Bounties"].split(",")
                categories.extend([b.strip() for b in bounties])

            # Remove duplicates
            categories = list(set(categories))

            # Create team entry
            teams.append(
                {"id": row["BUIDL ID"], "name": team_name, "categories": categories}
            )

        # Check if we have any teams
        if not teams:
            console.print(
                "[bold red]Error:[/bold red] No valid team data found in the CSV file"
            )
            sys.exit(1)

        return teams

    except Exception as e:
        console.print(f"[bold red]Error loading CSV file:[/bold red] {str(e)}")
        sys.exit(1)
