import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import csv
import os


def generate_judging_schedule(input_csv_path, output_dir="judging_schedules"):
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Read the input CSV
    projects_df = pd.read_csv(input_csv_path)

    # Extract relevant information
    teams = []
    for _, row in projects_df.iterrows():
        team_info = {
            "team_id": row["BUIDL ID"],
            "team_name": row["BUIDL name"],
            "team_contact": row["Contact email"],
            "team_members": row[
                "Please list ALL team members' first and last name separated by a comma:"
            ],
            "categories": [],
        }

        # Parse the track and bounties
        if pd.notna(row["Track"]):
            team_info["categories"].append(row["Track"])

        if pd.notna(row["Bounties"]):
            # Remove quotes and split by commas if multiple bounties
            bounties = row["Bounties"].replace('"', "")
            if "," in bounties:
                bounties_list = [b.strip() for b in bounties.split(",")]
                team_info["categories"].extend(bounties_list)
            else:
                team_info["categories"].append(bounties.strip())

        teams.append(team_info)

    # Define sponsor categories and rooms
    # Multiple rooms for general judging
    general_rooms = ["2nd floor Ideas clinic", "2462", "2462", "2458", "2456", "2454"]

    sponsor_categories = [
        {"name": "General", "rooms": general_rooms, "duration_minutes": 8},
        {
            "name": "MLH",
            "room": "1st floor Idea's clinic",
            "duration_minutes": 3,
            "subcategories": [
                "Best .Tech Domain Name",
                "Best Use of MongoDB Atlas",
                "Best Use of GenAI",
            ],
        },
        {"name": "Pico-Best 8 Prize", "room": "1st floor Idea's clinic", "duration_minutes": 3},
        {"name": "Best hackathon tool", "room": "1st floor Idea's clinic", "duration_minutes": 3},
        {"name": "Best dev tool", "room": "1st floor Idea's clinic", "duration_minutes": 3},
    ]

    # Create mapping of category to room and duration
    category_map = {}
    for category in sponsor_categories:
        if category["name"] == "General":
            category_map[category["name"]] = {
                "rooms": category["rooms"],
                "duration": category["duration_minutes"],
            }
        else:
            category_map[category["name"]] = {
                "room": category["room"],
                "duration": category["duration_minutes"],
            }
            if "subcategories" in category:
                category_map[category["name"]]["subcategories"] = category[
                    "subcategories"
                ]

    # Define start time and end time for judging
    start_time = datetime.strptime("10:30", "%H:%M")
    end_time = datetime.strptime("12:10", "%H:%M")

    # Create scheduling data structure
    schedule = {}
    for category in sponsor_categories:
        if category["name"] == "General":
            # Create separate schedules for each general room
            for room in category["rooms"]:
                schedule[f"General_{room}"] = []
        else:
            schedule[category["name"]] = []

    # Schedule general judging first, distributing teams across multiple rooms
    num_general_rooms = len(general_rooms)
    teams_per_room = np.array_split(teams, num_general_rooms)

    for room_idx, room_teams in enumerate(teams_per_room):
        current_time = start_time
        room = general_rooms[room_idx]

        for team in room_teams:
            # Check if we're exceeding the end time
            if current_time + timedelta(minutes=8) > end_time:
                print(
                    f"Warning: Scheduling would exceed end time for team {team['team_id']} in room {room}"
                )
                continue

            schedule[f"General_{room}"].append(
                {
                    "team_id": team["team_id"],
                    "team_name": team["team_name"],
                    "start_time": current_time,
                    "end_time": current_time + timedelta(minutes=8),
                    "room": room,
                }
            )
            current_time += timedelta(minutes=8)

    # Schedule sponsor-specific judging, avoiding conflicts
    for category in sponsor_categories:
        if category["name"] == "General":
            continue

        current_time = start_time
        for team in teams:
            # Check if the team is eligible for this category or its subcategories
            is_eligible = False

            # Check main category eligibility
            if category["name"] in team["categories"]:
                is_eligible = True

            # Check subcategory eligibility
            if "subcategories" in category:
                for subcategory in category["subcategories"]:
                    if subcategory in team["categories"]:
                        is_eligible = True
                        break

            if is_eligible:
                # Find a time slot that doesn't conflict with the team's other commitments
                is_conflict = True
                while is_conflict:
                    is_conflict = False

                    # Check if we're exceeding the end time
                    if (
                        current_time + timedelta(minutes=category["duration_minutes"])
                        > end_time
                    ):
                        print(
                            f"Warning: Scheduling would exceed end time for team {team['team_id']} in category {category['name']}"
                        )
                        break

                    # Check for conflicts with other schedules
                    for other_category, slots in schedule.items():
                        for slot in slots:
                            if slot["team_id"] == team["team_id"]:
                                # Check if current_time overlaps with this slot
                                slot_end = slot["end_time"]
                                slot_start = slot["start_time"]
                                proposed_end = current_time + timedelta(
                                    minutes=category["duration_minutes"]
                                )

                                if (
                                    (slot_start <= current_time < slot_end)
                                    or (slot_start < proposed_end <= slot_end)
                                    or (
                                        current_time <= slot_start
                                        and proposed_end >= slot_end
                                    )
                                ):
                                    is_conflict = True
                                    current_time = slot_end
                                    break
                        if is_conflict:
                            break

                # Skip if we couldn't find a slot before the end time
                if (
                    current_time + timedelta(minutes=category["duration_minutes"])
                    > end_time
                ):
                    continue

                # Add the schedule for this team and category
                schedule[category["name"]].append(
                    {
                        "team_id": team["team_id"],
                        "team_name": team["team_name"],
                        "start_time": current_time,
                        "end_time": current_time
                        + timedelta(minutes=category["duration_minutes"]),
                        "room": category_map[category["name"]]["room"],
                        "subcategories": category_map[category["name"]].get(
                            "subcategories", []
                        ),
                    }
                )
                current_time += timedelta(minutes=category["duration_minutes"])

    # Generate CSV for each judging room (for General category)
    for room in general_rooms:
        room_schedule = schedule[f"General_{room}"]

        with open(f"{output_dir}/Room_{room}_judging.csv", "w", newline="") as csvfile:
            fieldnames = [
                "TIMESLOT",
                "TEAM",
                "Creativity (/10)",
                "Usefulness (/10)",
                "Presentation (/10)",
                "Technical Difficulty (/10)",
            ]

            # Add all sponsor categories as columns
            for category in sponsor_categories:
                if category["name"] != "General":
                    if "subcategories" in category:
                        for subcategory in category["subcategories"]:
                            fieldnames.append(f"{subcategory} (/10)")
                    else:
                        fieldnames.append(f"{category['name']} (/10)")

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for slot in sorted(room_schedule, key=lambda x: x["start_time"]):
                row = {
                    "TIMESLOT": f"{slot['start_time'].strftime('%H:%M')} - {slot['end_time'].strftime('%H:%M')}",
                    "TEAM": f"{slot['team_id']} - {slot['team_name']}",
                    "Creativity (/10)": "",
                    "Usefulness (/10)": "",
                    "Presentation (/10)": "",
                    "Technical Difficulty (/10)": "",
                }

                # Add empty cells for category-specific columns
                for category in sponsor_categories:
                    if category["name"] != "General":
                        if "subcategories" in category:
                            for subcategory in category["subcategories"]:
                                row[f"{subcategory} (/10)"] = ""
                        else:
                            row[f"{category['name']} (/10)"] = ""

                writer.writerow(row)

    # Generate CSV for sponsor categories
    for category in sponsor_categories:
        if category["name"] == "General":
            continue

        room_schedule = schedule[category["name"]]
        room_name = (
            category_map[category["name"]]["room"].replace(" ", "_").replace("/", "_")
        )

        with open(f"{output_dir}/{room_name}_judging.csv", "w", newline="") as csvfile:
            fieldnames = [
                "TIMESLOT",
                "TEAM",
                "Creativity (/10)",
                "Usefulness (/10)",
                "Presentation (/10)",
                "Technical Difficulty (/10)",
            ]

            # For MLH and other categories with subcategories, add them as separate columns
            if "subcategories" in category:
                for subcategory in category["subcategories"]:
                    fieldnames.append(f"{subcategory} (/10)")

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for slot in sorted(room_schedule, key=lambda x: x["start_time"]):
                row = {
                    "TIMESLOT": f"{slot['start_time'].strftime('%H:%M')} - {slot['end_time'].strftime('%H:%M')}",
                    "TEAM": f"{slot['team_id']} - {slot['team_name']}",
                    "Creativity (/10)": "",
                    "Usefulness (/10)": "",
                    "Presentation (/10)": "",
                    "Technical Difficulty (/10)": "",
                }

                # Add subcategory columns if applicable
                if "subcategories" in category:
                    for subcategory in category["subcategories"]:
                        row[f"{subcategory} (/10)"] = ""

                writer.writerow(row)

    # Generate master schedule for hackers
    master_schedule = []

    # Add general judging slots to master schedule
    for room in general_rooms:
        for slot in schedule[f"General_{room}"]:
            master_schedule.append(
                {
                    "TEAM_ID": slot["team_id"],
                    "TEAM_NAME": slot["team_name"],
                    "TIME": f"{slot['start_time'].strftime('%H:%M')} - {slot['end_time'].strftime('%H:%M')}",
                    "ROOM": slot["room"],
                    "CATEGORY": "General",
                }
            )

    # Add sponsor category slots to master schedule
    for category_name, slots in schedule.items():
        if category_name.startswith("General_"):
            continue  # Skip the general rooms since we've already processed them

        for slot in slots:
            if "subcategories" in slot and slot["subcategories"]:
                # For categories with subcategories like MLH, add the subcategories to the category name
                subcats = ", ".join(slot["subcategories"])
                display_category = f"{category_name} ({subcats})"
            else:
                display_category = category_name

            master_schedule.append(
                {
                    "TEAM_ID": slot["team_id"],
                    "TEAM_NAME": slot["team_name"],
                    "TIME": f"{slot['start_time'].strftime('%H:%M')} - {slot['end_time'].strftime('%H:%M')}",
                    "ROOM": slot["room"],
                    "CATEGORY": display_category,
                }
            )

    # Sort master schedule by team and time
    master_schedule.sort(key=lambda x: (x["TEAM_ID"], x["TIME"]))

    # Write master schedule to CSV
    with open(f"{output_dir}/master_schedule.csv", "w", newline="") as csvfile:
        fieldnames = ["TEAM_ID", "TEAM_NAME", "TIME", "ROOM", "CATEGORY"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(master_schedule)

    print(f"Judging schedules generated in '{output_dir}' directory.")


if __name__ == "__main__":
    # Replace with actual path to your CSV file
    input_csv_path = "buidl_export(6).csv"
    generate_judging_schedule(input_csv_path)
