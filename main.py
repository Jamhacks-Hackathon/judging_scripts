import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import csv
import os

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
    
    # Define the exact sponsor categories as provided
    # For normalization, we'll strip quotes from the category names
    # and create a list of canonical names to avoid duplicates
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
    
    # Define rooms for the canonical categories
    category_rooms = {
        'General': {"rooms": ["2nd floor Idea's clinic", "2464", "2462", "2458", "2456", "2454"], "duration_minutes": 8},
        'MLH || Best .Tech Domain Name': {"room": "2nd floor Idea's clinic", "duration_minutes": 3},
        'MLH || Best Use of Gen AI': {"room": "2nd floor Idea's clinic", "duration_minutes": 3},
        'MLH || Best Use of MongoDB Atlas': {"room": "2nd floor Idea's clinic", "duration_minutes": 3},
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
    
    # Define start time and end time for judging
    start_time = datetime.strptime("10:35", "%H:%M")
    end_time = datetime.strptime("12:15", "%H:%M")
    
    # Create scheduling data structure
    schedule = {}
    
    # Initialize schedules for general rooms
    for room in category_rooms['General']["rooms"]:
        schedule[f"General_{room}"] = []
    
    # Initialize schedules for sponsor categories
    for category in all_category_names:
        # Skip MLH categories as they'll be handled together
        if category in mlh_categories[1:]:  # Skip all but the first MLH category
            continue
        schedule[category] = []
    
    # Schedule general judging first, distributing teams across multiple rooms
    general_rooms = category_rooms['General']["rooms"]
    num_general_rooms = len(general_rooms)
    teams_per_room = np.array_split(teams, num_general_rooms)
    
    for room_idx, room_teams in enumerate(teams_per_room):
        current_time = start_time
        room = general_rooms[room_idx]
        
        for team in room_teams:
            # Check if we're exceeding the end time
            if current_time + timedelta(minutes=8) > end_time:
                print(f"Warning: Scheduling would exceed end time for team {team['team_id']} in room {room}")
                continue
            
            schedule[f"General_{room}"].append({
                "team_id": team["team_id"],
                "team_name": team["team_name"],
                "start_time": current_time,
                "end_time": current_time + timedelta(minutes=8),
                "room": room
            })
            current_time += timedelta(minutes=8)
    
    # Schedule sponsor categories individually (except MLH which will be grouped)
    for category in all_category_names:
        # Skip MLH categories after the first one (we'll handle them together)
        if category in mlh_categories[1:]:
            continue
        
        # Get room info and duration
        room_info = category_rooms.get(category, {"room": "TBD", "duration_minutes": 3})
        
        # Set the starting time, applying delay if specified
        if category == 'Best Pico-8 Prize Track by Pex Labs':
            current_time = start_time + timedelta(minutes=room_info.get("delay_minutes", 0))
        else:
            current_time = start_time
        
        # For MLH categories, we'll look for teams that match any MLH category
        if category == mlh_categories[0]:  # First MLH category
            eligible_teams = [team for team in teams if any(mlh_cat in team["categories"] for mlh_cat in mlh_categories)]
        else:
            eligible_teams = [team for team in teams if category in team["categories"]]
        
        for team in eligible_teams:
            # Find a time slot that doesn't conflict with the team's other commitments
            is_conflict = True
            while is_conflict:
                is_conflict = False
                
                # Check if we're exceeding the end time
                if current_time + timedelta(minutes=room_info["duration_minutes"]) > end_time:
                    print(f"Warning: Scheduling would exceed end time for team {team['team_id']} in category {category}")
                    break
                
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
            
            # Skip if we couldn't find a slot before the end time
            if current_time + timedelta(minutes=room_info["duration_minutes"]) > end_time:
                continue
            
            # Add the schedule for this team and category
            slot_info = {
                "team_id": team["team_id"],
                "team_name": team["team_name"],
                "start_time": current_time,
                "end_time": current_time + timedelta(minutes=room_info["duration_minutes"]),
                "room": room_info["room"]
            }
            
            # For MLH categories, add which specific MLH categories the team is in
            if category == mlh_categories[0]:
                slot_info["mlh_categories"] = [cat for cat in mlh_categories if cat in team["categories"]]
            
            schedule[category].append(slot_info)
            current_time += timedelta(minutes=room_info["duration_minutes"])
    
    # Generate CSV for each judging room (for General category)
    for room in general_rooms:
        room_schedule = schedule[f"General_{room}"]
        
        with open(f'{output_dir}/Room_{room}_judging.csv', 'w', newline='') as csvfile:
            fieldnames = ['TIMESLOT', 'TEAM', 'Creativity (/10)', 'Usefulness (/10)',
                          'Presentation (/10)', 'Technical Difficulty (/10)']
            
            # Add all sponsor categories as columns
            for sponsor_category in all_category_names:
                fieldnames.append(f'{sponsor_category} (/10)')
            
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
                
                # Add empty cells for category-specific columns
                for sponsor_category in all_category_names:
                    row[f'{sponsor_category} (/10)'] = ''
                
                writer.writerow(row)
    
    # Generate CSV for sponsor categories
    for category in all_category_names:
        # Skip MLH categories after the first one
        if category in mlh_categories[1:]:
            continue
        
        room_info = category_rooms.get(category, {"room": "TBD", "duration_minutes": 3})
        room_name = room_info["room"].replace(" ", "_").replace("/", "_").replace("'", "")
        
        with open(f'{output_dir}/{room_name}_{category.replace(" ", "_").replace("|", "")}_judging.csv', 'w', newline='') as csvfile:
            fieldnames = ['TIMESLOT', 'TEAM', 'Creativity (/10)', 'Usefulness (/10)',
                          'Presentation (/10)', 'Technical Difficulty (/10)']
            
            # For MLH, add all MLH subcategories as columns
            if category == mlh_categories[0]:
                for mlh_cat in mlh_categories:
                    fieldnames.append(f'{mlh_cat} (/10)')
            
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
                
                # For MLH, add empty cells for all MLH category columns
                if category == mlh_categories[0]:
                    for mlh_cat in mlh_categories:
                        row[f'{mlh_cat} (/10)'] = ''
                
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
    
    # Add sponsor category slots to master schedule
    for category in all_category_names:
        # Skip MLH categories after the first one
        if category in mlh_categories[1:]:
            continue
        
        room_info = category_rooms.get(category, {"room": "TBD", "duration_minutes": 3})
        
        for slot in schedule[category]:
            if category == mlh_categories[0] and "mlh_categories" in slot:
                # For MLH, show which specific MLH categories the team is eligible for
                specific_categories = ", ".join(slot["mlh_categories"])
                display_category = f"MLH ({specific_categories})"
            else:
                display_category = category
            
            master_schedule.append({
                'TEAM_ID': slot['team_id'],
                'TEAM_NAME': slot['team_name'],
                'TIME': f"{slot['start_time'].strftime('%H:%M')} - {slot['end_time'].strftime('%H:%M')}",
                'ROOM': slot['room'],
                'CATEGORY': display_category
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