"""
Scheduling module for JAMHacks scheduler.

This module contains functions for generating judging schedules.
"""

import datetime
import copy

# Define constants
JUDGING_DURATION = 8  # minutes (1 setup + 3 pitch + 2 Q&A + 2 scoring)
MLH_CATEGORIES = ["Best Use of MongoDB", "Best GenAI", "Best .tech"]


def get_categories_from_teams(teams):
    """
    Extract all unique categories from team submissions.

    Args:
        teams (list): List of team dictionaries

    Returns:
        list: List of unique categories
    """
    all_categories = set()
    for team in teams:
        for category in team["categories"]:
            # Don't include MLH categories - they're handled together
            if category not in MLH_CATEGORIES:
                all_categories.add(category)

    return sorted(list(all_categories))


def generate_general_schedule(teams, start_time, buffer_minutes=8, num_rooms=6):
    """
    Generate general judging schedule for all teams.

    Args:
        teams (list): List of team dictionaries
        start_time (datetime): Start time
        buffer_minutes (int): Buffer time between teams in minutes
        num_rooms (int): Number of judging rooms

    Returns:
        tuple: (schedule, end_time) where schedule is a dictionary of room schedules
               and end_time is when the general judging ends
    """
    # Create a copy of the teams to avoid modifying the original
    teams_copy = copy.deepcopy(teams)

    # Identify teams with MLH categories
    mlh_teams = []
    non_mlh_teams = []

    for team in teams_copy:
        if any(cat in MLH_CATEGORIES for cat in team["categories"]):
            mlh_teams.append(team)
        else:
            non_mlh_teams.append(team)

    # Create room assignments dictionary
    room_assignments = {i + 1: [] for i in range(num_rooms)}

    # Reserve room 6 for MLH teams if we have enough MLH teams
    if len(mlh_teams) >= 6:
        room_assignments[6] = mlh_teams

        # Distribute remaining teams evenly across other rooms
        remaining_rooms = list(range(1, 6))
        teams_per_room = len(non_mlh_teams) // len(remaining_rooms)
        remaining = len(non_mlh_teams) % len(remaining_rooms)

        # Allocate teams to rooms
        team_index = 0
        for i, room_num in enumerate(remaining_rooms):
            # Calculate how many teams for this room
            count = teams_per_room + (1 if i < remaining else 0)
            room_assignments[room_num] = non_mlh_teams[team_index : team_index + count]
            team_index += count
    else:
        # If not enough MLH teams, put them all in room 6
        room_assignments[6] = mlh_teams

        # Distribute non-MLH teams evenly across all rooms
        # including room 6 if it's not full
        all_rooms = list(range(1, num_rooms + 1))

        # Calculate teams per room
        total_to_distribute = len(non_mlh_teams)
        base_per_room = total_to_distribute // num_rooms
        remainder = total_to_distribute % num_rooms

        # Allocate teams to rooms
        non_mlh_index = 0
        for room_num in all_rooms:
            # Skip if room 6 already has MLH teams
            if room_num == 6 and room_assignments[6]:
                continue

            # Calculate how many teams for this room
            count = base_per_room + (1 if remainder > 0 else 0)
            remainder -= 1 if remainder > 0 else 0

            room_assignments[room_num].extend(
                non_mlh_teams[non_mlh_index : non_mlh_index + count]
            )
            non_mlh_index += count

    # Generate schedule
    schedule = {}
    room_end_times = {}
    team_schedules = {}  # Track when each team is scheduled (for avoiding conflicts)

    for room_num, room_teams in room_assignments.items():
        schedule[room_num] = []
        current_time = start_time

        for team in room_teams:
            # Create schedule entry
            end_time = current_time + datetime.timedelta(minutes=JUDGING_DURATION)

            schedule_entry = {
                "team_id": team["id"],
                "team_name": team["name"],
                "type": "General",
                "categories": team["categories"],
                "start_time": current_time,
                "end_time": end_time,
            }

            schedule[room_num].append(schedule_entry)

            # Track this team's schedule
            if team["id"] not in team_schedules:
                team_schedules[team["id"]] = []
            team_schedules[team["id"]].append(
                {"start_time": current_time, "end_time": end_time, "type": "General"}
            )

            # Move to next time slot
            current_time = end_time + datetime.timedelta(minutes=buffer_minutes)

        # Record when this room finishes
        if room_teams:
            room_end_times[room_num] = schedule[room_num][-1]["end_time"]
        else:
            room_end_times[room_num] = start_time

    # Return schedule and the latest end time
    latest_end_time = max(room_end_times.values()) if room_end_times else start_time
    return schedule, latest_end_time, team_schedules


def generate_category_schedules(teams, start_time, team_schedules, buffer_minutes=8):
    """
    Generate schedules for category-specific judging.

    Args:
        teams (list): List of team dictionaries
        start_time (datetime): Start time for category judging
        team_schedules (dict): Dictionary tracking when each team is already scheduled
        buffer_minutes (int): Buffer time between teams

    Returns:
        dict: Category schedules {category: [team1, team2, ...]}
    """
    # First, identify all non-MLH categories
    all_categories = get_categories_from_teams(teams)

    # Create a schedule for each category
    category_schedules = {}

    # Also create an MLH schedule
    category_schedules["MLH"] = []

    # For each non-MLH category, create a schedule
    for category in all_categories:
        category_schedules[category] = []

    # Find teams for each category
    category_teams = {cat: [] for cat in all_categories}
    category_teams["MLH"] = []

    for team in teams:
        # Check for MLH categories first
        if any(cat in MLH_CATEGORIES for cat in team["categories"]):
            category_teams["MLH"].append(team)

        # Check for non-MLH categories
        for cat in team["categories"]:
            if cat in all_categories:
                category_teams[cat].append(team)

    # Generate schedule for each category
    current_start_time = start_time

    # First schedule MLH since it's special
    if category_teams["MLH"]:
        current_time = current_start_time

        for team in category_teams["MLH"]:
            # Check for conflicts with team's existing schedule
            conflict = False
            earliest_available = current_time

            if team["id"] in team_schedules:
                for existing in team_schedules[team["id"]]:
                    # Check if this time conflicts with existing schedule
                    # Allow buffer_minutes between different judging sessions
                    proposed_end = current_time + datetime.timedelta(
                        minutes=JUDGING_DURATION
                    )

                    if (
                        current_time
                        <= existing["end_time"]
                        + datetime.timedelta(minutes=buffer_minutes)
                        and proposed_end + datetime.timedelta(minutes=buffer_minutes)
                        >= existing["start_time"]
                    ):
                        # Conflict found - schedule after the existing slot
                        conflict = True
                        conflict_end = existing["end_time"] + datetime.timedelta(
                            minutes=buffer_minutes
                        )
                        if conflict_end > earliest_available:
                            earliest_available = conflict_end

            # Use the earliest available time if there was a conflict
            if conflict:
                current_time = earliest_available

            # Schedule the team
            end_time = current_time + datetime.timedelta(minutes=JUDGING_DURATION)

            category_schedules["MLH"].append(
                {
                    "team_id": team["id"],
                    "team_name": team["name"],
                    "type": "MLH",
                    "categories": [
                        cat for cat in team["categories"] if cat in MLH_CATEGORIES
                    ],
                    "start_time": current_time,
                    "end_time": end_time,
                }
            )

            # Update team's schedule
            if team["id"] not in team_schedules:
                team_schedules[team["id"]] = []
            team_schedules[team["id"]].append(
                {"start_time": current_time, "end_time": end_time, "type": "MLH"}
            )

            # Move to next time slot
            current_time = end_time + datetime.timedelta(minutes=buffer_minutes)

        # Set start time for next category
        if category_schedules["MLH"]:
            current_start_time = category_schedules["MLH"][-1][
                "end_time"
            ] + datetime.timedelta(minutes=buffer_minutes)

    # Schedule remaining categories
    for category in all_categories:
        if not category_teams[category]:
            continue

        current_time = current_start_time

        for team in category_teams[category]:
            # Check for conflicts with team's existing schedule
            conflict = False
            earliest_available = current_time

            if team["id"] in team_schedules:
                for existing in team_schedules[team["id"]]:
                    # Check if this time conflicts with existing schedule
                    # Allow buffer_minutes between different judging sessions
                    proposed_end = current_time + datetime.timedelta(
                        minutes=JUDGING_DURATION
                    )

                    if (
                        current_time
                        <= existing["end_time"]
                        + datetime.timedelta(minutes=buffer_minutes)
                        and proposed_end + datetime.timedelta(minutes=buffer_minutes)
                        >= existing["start_time"]
                    ):
                        # Conflict found - schedule after the existing slot
                        conflict = True
                        conflict_end = existing["end_time"] + datetime.timedelta(
                            minutes=buffer_minutes
                        )
                        if conflict_end > earliest_available:
                            earliest_available = conflict_end

            # Use the earliest available time if there was a conflict
            if conflict:
                current_time = earliest_available

            # Schedule the team
            end_time = current_time + datetime.timedelta(minutes=JUDGING_DURATION)

            category_schedules[category].append(
                {
                    "team_id": team["id"],
                    "team_name": team["name"],
                    "type": category,
                    "categories": [category],
                    "start_time": current_time,
                    "end_time": end_time,
                }
            )

            # Update team's schedule
            if team["id"] not in team_schedules:
                team_schedules[team["id"]] = []
            team_schedules[team["id"]].append(
                {"start_time": current_time, "end_time": end_time, "type": category}
            )

            # Move to next time slot
            current_time = end_time + datetime.timedelta(minutes=buffer_minutes)

        # Set start time for next category
        if category_schedules[category]:
            current_start_time = category_schedules[category][-1][
                "end_time"
            ] + datetime.timedelta(minutes=buffer_minutes)

    return category_schedules


def generate_schedule(teams, start_time_str, buffer_minutes=8, num_rooms=6):
    """
    Generate complete judging schedule including general and category-specific judging.

    Args:
        teams (list): List of team dictionaries
        start_time_str (str): Start time in the format 'YYYY-MM-DD HH:MM'
        buffer_minutes (int): Buffer time between teams in minutes
        num_rooms (int): Number of judging rooms

    Returns:
        tuple: (schedule, stats) where schedule contains all schedules
               and stats contains schedule statistics
    """
    # Parse start time
    start_time = datetime.datetime.strptime(start_time_str, "%Y-%m-%d %H:%M")

    # Generate general schedule
    general_schedule, general_end_time, team_schedules = generate_general_schedule(
        teams, start_time, buffer_minutes, num_rooms
    )

    # Generate category schedules (starts after general judging)
    category_schedules = generate_category_schedules(
        teams,
        general_end_time + datetime.timedelta(minutes=30),  # 30-min break after general
        team_schedules,
        buffer_minutes,
    )

    # Calculate the latest end time from all schedules
    latest_end_time = general_end_time
    for category, schedule in category_schedules.items():
        if schedule:
            category_end_time = schedule[-1]["end_time"]
            if category_end_time > latest_end_time:
                latest_end_time = category_end_time

    # Calculate schedule statistics
    stats = {
        "start_time": start_time,
        "general_end_time": general_end_time,
        "end_time": latest_end_time,
        "total_teams": len(teams),
        "general_rooms": {room: len(slots) for room, slots in general_schedule.items()},
        "categories": list(category_schedules.keys()),
    }

    # Create combined schedule data
    schedule = {"general": general_schedule, "categories": category_schedules}

    return schedule, stats
