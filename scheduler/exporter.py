"""
Export module for JAMHacks scheduler.

This module contains functions for exporting schedules to different formats.
"""

import os
import csv
import datetime
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import warnings

# Suppress matplotlib warnings
warnings.filterwarnings("ignore")


def export_schedules(schedule, stats, output_dir):
    """
    Generate CSV files with the schedule.

    Args:
            schedule (dict): Schedule dictionary
    stats (dict): Schedule statistics
    output_dir (str): Output directory path

    Returns:
    list: List of generated file paths
    """

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    output_files = []

    # Master general schedule
    master_file = os.path.join(output_dir, "general_schedule.csv")
    output_files.append(master_file)

    with open(master_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Room", "Team", "Start Time", "Categories"])

        for room_num, room_schedule in schedule["general"].items():
            for slot in room_schedule:
                writer.writerow(
                    [
                        room_num,
                        slot["team_name"],
                        slot["start_time"].strftime("%I:%M %p"),
                        ", ".join(slot["categories"]),
                    ]
                )

    # Individual room schedules for general judging
    for room_num, room_schedule in schedule["general"].items():
        room_file = os.path.join(output_dir, f"room_{room_num}_schedule.csv")
        output_files.append(room_file)

        with open(room_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Room", "Team", "Start Time"])

            for slot in room_schedule:
                writer.writerow(
                    [
                        room_num,
                        slot["team_name"],
                        slot["start_time"].strftime("%I:%M %p"),
                    ]
                )

    # Category schedules
    for category, category_schedule in schedule["categories"].items():
        if not category_schedule:
            continue

        category_file = os.path.join(output_dir, f"{category}_schedule.csv")
        output_files.append(category_file)

        with open(category_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Category", "Team", "Start Time"])

            for slot in category_schedule:
                writer.writerow(
                    [
                        category,
                        slot["team_name"],
                        slot["start_time"].strftime("%I:%M %p"),
                    ]
                )

    # Team lookup schedule (all judging sessions for each team)
    team_file = os.path.join(output_dir, "team_schedule.csv")
    output_files.append(team_file)

    with open(team_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Team", "Session Type", "Location", "Start Time"])

        # Collect all team schedules
        team_schedules = {}

        # Add general judging
        for room_num, room_schedule in schedule["general"].items():
            for slot in room_schedule:
                team_id = slot["team_id"]
                team_name = slot["team_name"]

                if team_id not in team_schedules:
                    team_schedules[team_id] = {"name": team_name, "sessions": []}

                team_schedules[team_id]["sessions"].append(
                    {
                        "type": "General",
                        "location": f"Room {room_num}",
                        "start_time": slot["start_time"],
                    }
                )

        # Add category judging
        for category, category_schedule in schedule["categories"].items():
            for slot in category_schedule:
                team_id = slot["team_id"]
                team_name = slot["team_name"]

                if team_id not in team_schedules:
                    team_schedules[team_id] = {"name": team_name, "sessions": []}

                team_schedules[team_id]["sessions"].append(
                    {
                        "type": category,
                        "location": f"{category} Judging",
                        "start_time": slot["start_time"],
                    }
                )

        # Sort by team ID and then by start time
        for team_id in sorted(team_schedules.keys()):
            team = team_schedules[team_id]
            # Sort sessions by start time
            sessions = sorted(team["sessions"], key=lambda x: x["start_time"])

            for session in sessions:
                writer.writerow(
                    [
                        team["name"],
                        session["type"],
                        session["location"],
                        session["start_time"].strftime("%I:%M %p"),
                    ]
                )

    return output_files


def generate_visualizations(schedule, stats, output_dir):
    """
    Generate visualizations of the schedule.

    Args:
    schedule (dict): Schedule dictionary
    stats (dict): Schedule statistics
    output_dir (str): Output directory path

    Returns:
    list: List of generated visualization file paths
    """
    os.makedirs(output_dir, exist_ok=True)
    output_files = []

    # 1. Create Gantt chart of the general schedule
    plt.figure(figsize=(12, 8))
    ax = plt.gca()

    # Set up colors
    colors = plt.cm.tab10(np.linspace(0, 1, len(schedule["general"])))

    # Convert times to numbers for plotting
    y_ticks = []
    y_labels = []

    for i, (room_num, room_schedule) in enumerate(schedule["general"].items()):
        y_pos = len(schedule["general"]) - i
        y_ticks.append(y_pos)
        y_labels.append(f"Room {room_num}")

        for j, slot in enumerate(room_schedule):
            # Convert datetime to minutes since start
            start = (
                slot["start_time"].timestamp() - stats["start_time"].timestamp()
            ) / 60
            duration = (
                slot["end_time"].timestamp() - slot["start_time"].timestamp()
            ) / 60

            # Plot the team slot
            ax.barh(
                y_pos,
                duration,
                left=start,
                height=0.5,
                color=colors[i % len(colors)],
                alpha=0.8,
                edgecolor="black",
                linewidth=0.5,
            )

            # Add team name as text
            plt.text(
                start + duration / 2,
                y_pos,
                slot["team_name"],
                ha="center",
                va="center",
                fontsize=8,
                color="black",
            )

    # Set up the axes
    plt.yticks(y_ticks, y_labels)

    # Format x-axis as time
    def format_func(x, pos):
        minutes = int(x)
        dt = stats["start_time"] + datetime.timedelta(minutes=minutes)
        return dt.strftime("%I:%M %p")

    from matplotlib.ticker import FuncFormatter

    ax.xaxis.set_major_formatter(FuncFormatter(format_func))
    plt.xticks(rotation=45)

    # Set labels and title
    plt.title("JAMHacks 9 General Judging Schedule", fontsize=16)
    plt.xlabel("Time")
    plt.ylabel("Room")

    plt.tight_layout()
    gantt_file = os.path.join(output_dir, "general_schedule_gantt.png")
    plt.savefig(gantt_file, dpi=300)
    output_files.append(gantt_file)

    # 2. Create room load barplot
    plt.figure(figsize=(10, 6))

    # Prepare data
    room_nums = list(stats["general_rooms"].keys())
    team_counts = list(stats["general_rooms"].values())

    # Create barplot
    sns.barplot(x=room_nums, y=team_counts, palette="viridis")
    plt.title("Teams per Judging Room", fontsize=16)
    plt.xlabel("Room Number")
    plt.ylabel("Number of Teams")

    # Add the exact count on top of each bar
    for i, count in enumerate(team_counts):
        plt.text(i, count + 0.1, str(count), ha="center")

    plt.tight_layout()
    heatmap_file = os.path.join(output_dir, "room_load.png")
    plt.savefig(heatmap_file, dpi=300)
    output_files.append(heatmap_file)

    # 3. Create category judging timelines
    non_empty_categories = [
        cat for cat, sched in schedule["categories"].items() if sched
    ]

    if non_empty_categories:
        plt.figure(figsize=(14, 8))
        ax = plt.gca()

        # Set up colors
        colors = plt.cm.tab20(np.linspace(0, 1, len(non_empty_categories)))

        # Convert times to numbers for plotting
        y_ticks = []
        y_labels = []

        for i, category in enumerate(non_empty_categories):
            category_schedule = schedule["categories"][category]
            y_pos = len(non_empty_categories) - i
            y_ticks.append(y_pos)
            y_labels.append(category)

            for j, slot in enumerate(category_schedule):
                # Convert datetime to minutes since category judging start
                start = (
                    slot["start_time"].timestamp()
                    - stats["general_end_time"].timestamp()
                ) / 60
                duration = (
                    slot["end_time"].timestamp() - slot["start_time"].timestamp()
                ) / 60

                # Plot the team slot
                ax.barh(
                    y_pos,
                    duration,
                    left=start,
                    height=0.5,
                    color=colors[i % len(colors)],
                    alpha=0.8,
                    edgecolor="black",
                    linewidth=0.5,
                )

                # Add team name as text
                plt.text(
                    start + duration / 2,
                    y_pos,
                    slot["team_name"],
                    ha="center",
                    va="center",
                    fontsize=8,
                    color="black",
                )

        # Set up the axes
        plt.yticks(y_ticks, y_labels)

        # Format x-axis as time
        def format_func(x, pos):
            minutes = int(x)
            dt = stats["general_end_time"] + datetime.timedelta(minutes=minutes)
            return dt.strftime("%I:%M %p")

        from matplotlib.ticker import FuncFormatter

        ax.xaxis.set_major_formatter(FuncFormatter(format_func))
        plt.xticks(rotation=45)

        # Set labels and title
        plt.title("JAMHacks 9 Category Judging Schedule", fontsize=16)
        plt.xlabel("Time")
        plt.ylabel("Category")

        plt.tight_layout()
        category_file = os.path.join(output_dir, "category_schedule_gantt.png")
        plt.savefig(category_file, dpi=300)
        output_files.append(category_file)

    return output_files
