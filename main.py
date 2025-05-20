import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import csv
import os

# Define non-sponsor categories to be judged during general judging
NONSPONSOR_CATEGORIES = ["Best Beginner Hack", "Best Solo Hack", "Best Female Hack"]

def generate_judging_schedule(input_csv_path, output_dir='judging_schedules'):
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Read the input CSV
    projects_df = pd.read_csv(input_csv_path)
    
    # Extract relevant information
    teams = []
    for _, row in projects_df.iterrows():
        team_info = {
            'team_id': row['BUIDL ID'],
            'team_name': row['BUIDL name'],
            'team_contact': row['Contact email'],
            'team_members': row['Please list ALL team members\' first and last name separated by a comma:'],
            'categories': []
        }
        
        # Parse the track and bounties
        if pd.notna(row['Track']):
            team_info['categories'].append(row['Track'])
        
        if pd.notna(row['Bounties']):
            # Remove quotes and split by commas if multiple bounties
            bounties = row['Bounties'].replace('"', '')
            if ',' in bounties:
                bounties_list = [b.strip() for b in bounties.split(',')]
                team_info['categories'].extend(bounties_list)
            else:
                team_info['categories'].append(bounties.strip())
        
        teams.append(team_info)
    
    # Define MLH categories and search terms
    mlh_keywords = ["MLH", ".Tech", "MongoDB", "Gen AI"]
    
    # Define the exact sponsor categories as provided
    all_category_names = [
        'Best Developer Tool by Warp',
        'MLH || Best .Tech Domain Name',
        'MLH || Best Use of Gen AI',
        'MLH || Best Use of MongoDB Atlas',
        'Best Pico-8 Prize Track by Pex Labs',
        'Hackathon Tool Prize Track by Hack Canada'
    ]
    
    # Define a function to normalize category names (strip quotes and trailing/leading spaces)
    def normalize_category(category):
        return category.replace('"', '').strip()
    
    # Normalize team categories
    for team in teams:
        team['categories'] = [normalize_category(cat) for cat in team['categories']]
    
    # Print debug info
    print(f"Total teams: {len(teams)}")
    
    # Define rooms for the canonical categories
    category_rooms = {
        'General': {"rooms": ["2nd floor Idea's clinic", "2464", "2462", "2458", "2456", "2454"], "duration_minutes": 8},
        'MLH': {"room": "2nd floor Idea's clinic", "duration_minutes": 3}, # Using a generic MLH key
        'Best Developer Tool by Warp': {"room": "2430", "duration_minutes": 3},
        'Best Pico-8 Prize Track by Pex Labs': {"room": "2410", "duration_minutes": 3, "delay_minutes": 65},
        'Hackathon Tool Prize Track by Hack Canada': {"room": "2420", "duration_minutes": 3}
    }
    
    # Group MLH categories together
    mlh_categories = [
        'MLH || Best .Tech Domain Name',
        'MLH || Best Use of Gen AI',
        'MLH || Best Use of MongoDB Atlas'
    ]
    
    # Define start time for judging (soft deadline, will schedule past if needed)
    start_time = datetime.strptime("x11:05", "%H:%M")
    target_end_time = datetime.strptime("12:15", "%H:%M")
    
    # Create scheduling data structure
    schedule = {}
    
    # Initialize schedules for general rooms
    for room in category_rooms['General']["rooms"]:
        schedule[f"General_{room}"] = []
    
    # Initialize schedules for sponsor categories
    schedule['MLH'] = []  # Single entry for all MLH categories
    
    for category in all_category_names:
        if not category.startswith('MLH ||'):  # Skip individual MLH categories
            schedule[category] = []
    
    # Schedule general judging first, distributing teams across multiple rooms
    general_rooms = category_rooms['General']["rooms"]
    num_general_rooms = len(general_rooms)
    teams_per_room = np.array_split(teams, num_general_rooms)
    
    for room_idx, room_teams in enumerate(teams_per_room):
        current_time = start_time
        room = general_rooms[room_idx]
        
        for team in room_teams:
            # No longer checking if exceeding end time - schedule all teams
            schedule[f"General_{room}"].append({
                "team_id": team["team_id"],
                "team_name": team["team_name"],
                "start_time": current_time,
                "end_time": current_time + timedelta(minutes=8),
                "room": room
            })
            current_time += timedelta(minutes=8)
        
        # Print info about scheduling exceeding target end time
        if current_time > target_end_time:
            print(f"Note: General judging in room {room} extends to {current_time.strftime('%H:%M')}")
    
    # Find MLH teams
    mlh_teams = []
    
    # Find teams eligible for any MLH category by checking for MLH keywords in categories
    for team in teams:
        is_mlh_team = False
        team_mlh_categories = []
        
        for cat in team['categories']:
            # Check for MLH exact match
            if any(mlh_cat in cat for mlh_cat in mlh_categories):
                is_mlh_team = True
                team_mlh_categories.append(cat)
            # Check for MLH || prefix
            elif "MLH ||" in cat:
                is_mlh_team = True
                team_mlh_categories.append(cat)
            # Check for just "MLH"
            elif cat.startswith("MLH"):
                is_mlh_team = True
                team_mlh_categories.append(cat)
            # Check for any of the MLH keywords
            elif any(keyword.lower() in cat.lower() for keyword in mlh_keywords):
                is_mlh_team = True
                team_mlh_categories.append(cat)
        
        # If no specific MLH categories found but matches keywords, add generic MLH category
        if is_mlh_team and not team_mlh_categories:
            team_mlh_categories = ["MLH"]
        
        if is_mlh_team:
            mlh_teams.append({
                "team": team,
                "mlh_categories": team_mlh_categories
            })
    
    print(f"MLH teams found: {len(mlh_teams)}")
    
    # Schedule all MLH teams
    mlh_current_time = start_time
    for mlh_team in mlh_teams:
        team = mlh_team["team"]
        team_mlh_categories = mlh_team["mlh_categories"]
        
        # Find a time slot that doesn't conflict with the team's other commitments
        is_conflict = True
        while is_conflict:
            is_conflict = False
            
            # Check for conflicts with other schedules
            for category, slots in schedule.items():
                for slot in slots:
                    if slot["team_id"] == team["team_id"]:
                        # Check if current_time overlaps with this slot
                        slot_end = slot["end_time"]
                        slot_start = slot["start_time"]
                        proposed_end = mlh_current_time + timedelta(minutes=3)
                        
                        if (slot_start <= mlh_current_time < slot_end) or \
                                (slot_start < proposed_end <= slot_end) or \
                                (mlh_current_time <= slot_start and proposed_end >= slot_end):
                            is_conflict = True
                            mlh_current_time = slot_end
                            break
                if is_conflict:
                    break
        
        # Always schedule, regardless of time
        schedule['MLH'].append({
            "team_id": team["team_id"],
            "team_name": team["team_name"],
            "start_time": mlh_current_time,
            "end_time": mlh_current_time + timedelta(minutes=3),
            "room": category_rooms['MLH']["room"],
            "mlh_categories": team_mlh_categories
        })
        mlh_current_time += timedelta(minutes=3)
    
    # Print MLH scheduling info
    print(f"MLH judging scheduled from {start_time.strftime('%H:%M')} to {mlh_current_time.strftime('%H:%M')}")
    print(f"Scheduled MLH teams: {len(schedule['MLH'])}")
    
    # Schedule other sponsor categories
    for category in all_category_names:
        if category.startswith('MLH ||'):
            continue  # Skip individual MLH categories as they're handled together
        
        # Get room info and duration
        room_info = category_rooms.get(category, {"room": "TBD", "duration_minutes": 3})
        
        # Set the starting time, applying delay if specified
        if category == 'Best Pico-8 Prize Track by Pex Labs':
            current_time = start_time + timedelta(minutes=room_info.get("delay_minutes", 0))
        else:
            current_time = start_time
        
        eligible_teams = []
        for team in teams:
            # Check if team is eligible for this category
            for cat in team["categories"]:
                if category.lower() in cat.lower() or category.split(" by ")[0].lower() in cat.lower():
                    eligible_teams.append(team)
                    break
        
        print(f"Teams for {category}: {len(eligible_teams)}")
        
        for team in eligible_teams:
            # Find a time slot that doesn't conflict with the team's other commitments
            is_conflict = True
            while is_conflict:
                is_conflict = False
                
                # Check for conflicts with other schedules
                for other_category, slots in schedule.items():
                    for slot in slots:
                        if slot["team_id"] == team["team_id"]:
                            # Check if current_time overlaps with this slot
                            slot_end = slot["end_time"]
                            slot_start = slot["start_time"]
                            proposed_end = current_time + timedelta(minutes=room_info["duration_minutes"])
                            
                            if (slot_start <= current_time < slot_end) or \
                                    (slot_start < proposed_end <= slot_end) or \
                                    (current_time <= slot_start and proposed_end >= slot_end):
                                is_conflict = True
                                current_time = slot_end
                                break
                    if is_conflict:
                        break
            
            # Always schedule, regardless of time
            schedule[category].append({
                "team_id": team["team_id"],
                "team_name": team["team_name"],
                "start_time": current_time,
                "end_time": current_time + timedelta(minutes=room_info["duration_minutes"]),
                "room": room_info["room"]
            })
            current_time += timedelta(minutes=room_info["duration_minutes"])
        
        # Print category scheduling info
        if eligible_teams:
            print(f"{category} judging scheduled from {start_time.strftime('%H:%M')} to {current_time.strftime('%H:%M')}")
    
    # Generate CSV for each judging room (for General category)
    for room in general_rooms:
        room_schedule = schedule[f"General_{room}"]
        room_name = room.replace(" ", "_").replace("/", "_").replace("'", "")
        
        with open(f'{output_dir}/Room_{room_name}_judging.csv', 'w', newline='') as csvfile:
            fieldnames = ['TIMESLOT', 'TEAM', 'Creativity (/10)', 'Usefulness (/10)',
                          'Presentation (/10)', 'Technical Difficulty (/10)']
            
            # Add non-sponsor categories as columns for general judging
            for category in NONSPONSOR_CATEGORIES:
                fieldnames.append(f'{category} (/10)')
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for slot in sorted(room_schedule, key=lambda x: x["start_time"]):
                row = {
                    'TIMESLOT': f"{slot['start_time'].strftime('%H:%M')} - {slot['end_time'].strftime('%H:%M')}",
                    'TEAM': f"{slot['team_id']} - {slot['team_name']}",
                    'Creativity (/10)': '',
                    'Usefulness (/10)': '',
                    'Presentation (/10)': '',
                    'Technical Difficulty (/10)': ''
                }
                
                # Add empty cells for non-sponsor category columns
                for category in NONSPONSOR_CATEGORIES:
                    row[f'{category} (/10)'] = ''
                
                writer.writerow(row)
    
    # Generate CSV for MLH judging
    with open(f'{output_dir}/2nd_floor_Ideas_clinic_MLH_judging.csv', 'w', newline='') as csvfile:
        fieldnames = ['TIMESLOT', 'TEAM', 'Creativity (/10)', 'Usefulness (/10)',
                      'Presentation (/10)', 'Technical Difficulty (/10)']
        
        # Add all MLH subcategories as columns
        for mlh_cat in mlh_categories:
            fieldnames.append(f'{mlh_cat} (/10)')
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for slot in sorted(schedule['MLH'], key=lambda x: x["start_time"]):
            row = {
                'TIMESLOT': f"{slot['start_time'].strftime('%H:%M')} - {slot['end_time'].strftime('%H:%M')}",
                'TEAM': f"{slot['team_id']} - {slot['team_name']}",
                'Creativity (/10)': '',
                'Usefulness (/10)': '',
                'Presentation (/10)': '',
                'Technical Difficulty (/10)': ''
            }
            
            # Add empty cells for all MLH category columns
            for mlh_cat in mlh_categories:
                row[f'{mlh_cat} (/10)'] = ''
            
            writer.writerow(row)
    
    # Generate CSV for other sponsor categories
    for category in all_category_names:
        if category.startswith('MLH ||'):
            continue  # Skip individual MLH categories as they're handled together
        
        room_info = category_rooms.get(category, {"room": "TBD", "duration_minutes": 3})
        room_name = room_info["room"].replace(" ", "_").replace("/", "_").replace("'", "")
        category_filename = category.replace(" ", "_").replace("|", "").replace("'", "")
        
        with open(f'{output_dir}/{room_name}_{category_filename}_judging.csv', 'w', newline='') as csvfile:
            fieldnames = ['TIMESLOT', 'TEAM', 'Creativity (/10)', 'Usefulness (/10)',
                          'Presentation (/10)', 'Technical Difficulty (/10)']
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for slot in sorted(schedule[category], key=lambda x: x["start_time"]):
                row = {
                    'TIMESLOT': f"{slot['start_time'].strftime('%H:%M')} - {slot['end_time'].strftime('%H:%M')}",
                    'TEAM': f"{slot['team_id']} - {slot['team_name']}",
                    'Creativity (/10)': '',
                    'Usefulness (/10)': '',
                    'Presentation (/10)': '',
                    'Technical Difficulty (/10)': ''
                }
                
                writer.writerow(row)
    
    # Generate master schedule for hackers
    master_schedule = []
    
    # Add general judging slots to master schedule
    for room in general_rooms:
        for slot in schedule[f"General_{room}"]:
            master_schedule.append({
                'TEAM_ID': slot['team_id'],
                'TEAM_NAME': slot['team_name'],
                'TIME': f"{slot['start_time'].strftime('%H:%M')} - {slot['end_time'].strftime('%H:%M')}",
                'ROOM': slot['room'],
                'CATEGORY': "General"
            })
    
    # Add MLH judging slots to master schedule
    for slot in schedule['MLH']:
        # For MLH, show which specific MLH categories the team is eligible for
        if "mlh_categories" in slot:
            specific_categories = ", ".join(slot["mlh_categories"])
            display_category = f"MLH ({specific_categories})"
        else:
            display_category = "MLH"
        
        master_schedule.append({
            'TEAM_ID': slot['team_id'],
            'TEAM_NAME': slot['team_name'],
            'TIME': f"{slot['start_time'].strftime('%H:%M')} - {slot['end_time'].strftime('%H:%M')}",
            'ROOM': slot['room'],
            'CATEGORY': display_category
        })
    
    # Add other sponsor category slots to master schedule
    for category in all_category_names:
        if category.startswith('MLH ||'):
            continue  # Skip individual MLH categories as they're handled together
        
        for slot in schedule[category]:
            master_schedule.append({
                'TEAM_ID': slot['team_id'],
                'TEAM_NAME': slot['team_name'],
                'TIME': f"{slot['start_time'].strftime('%H:%M')} - {slot['end_time'].strftime('%H:%M')}",
                'ROOM': slot['room'],
                'CATEGORY': category
            })
    
    # Sort master schedule by team and time
    master_schedule.sort(key=lambda x: (x['TEAM_ID'], x['TIME']))
    
    # Write master schedule to CSV
    with open(f'{output_dir}/master_schedule.csv', 'w', newline='') as csvfile:
        fieldnames = ['TEAM_ID', 'TEAM_NAME', 'TIME', 'ROOM', 'CATEGORY']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(master_schedule)
    
    print(f"Judging schedules generated in '{output_dir}' directory.")


if __name__ == "__main__":
    # Replace with actual path to your CSV file
    input_csv_path = "buidl_export(8).csv"
    generate_judging_schedule(input_csv_path)