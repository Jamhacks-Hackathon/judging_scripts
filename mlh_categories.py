import pandas as pd
import csv

def enhance_mlh_schedule(input_csv_path, projects_csv_path, output_csv_path):
	"""
	Enhance the MLH judging schedule by:
	1. Adding the specific bounties/categories each team submitted to
	2. Removing team ID from the display
	
	Args:
		input_csv_path: Path to the MLH judging schedule CSV
		projects_csv_path: Path to the main projects data CSV
		output_csv_path: Path to save the enhanced schedule
	"""
	print(f"Processing MLH schedule from: {input_csv_path}")
	
	mlh_schedule = []
	try:
		with open(input_csv_path, 'r', newline='', encoding='utf-8') as csvfile:
			reader = csv.DictReader(csvfile)
			for row in reader:
				mlh_schedule.append(row)
	except Exception as e:
		print(f"Error reading MLH schedule: {e}")
		return
	
	print(f"Read {len(mlh_schedule)} entries from MLH schedule")
	
	# Read the project data to get categories/bounties
	try:
		projects_df = pd.read_csv(projects_csv_path)
		print(f"Read {len(projects_df)} projects from main CSV")
	except Exception as e:
		print(f"Error reading projects CSV: {e}")
		return
	
	team_categories = {}
	
	for _, row in projects_df.iterrows():
		team_name = row['BUIDL name']
		
		categories = []
		
		# Add track if available
		if pd.notna(row['Track']):
			categories.append(row['Track'])
		
		# Add bounties if available
		if pd.notna(row['Bounties']):
			# Parse bounties
			bounties = row['Bounties'].replace('"', '')
			if ',' in bounties:
				bounties_list = [b.strip() for b in bounties.split(',')]
				categories.extend(bounties_list)
			else:
				categories.append(bounties.strip())
		
		# Filter to only MLH-related categories
		mlh_keywords = ["MLH", ".Tech", "MongoDB", "Gen AI"]
		mlh_categories = []
		
		for cat in categories:
			if any(keyword.lower() in cat.lower() for keyword in mlh_keywords):
				mlh_categories.append(cat)
		
		if team_name:
			team_categories[team_name] = mlh_categories
	
	enhanced_schedule = []
	
	for entry in mlh_schedule:
		# Extract team name without ID
		if 'TEAM' in entry and '-' in entry['TEAM']:
			parts = entry['TEAM'].split(' - ', 1)
			if len(parts) > 1:
				team_id = parts[0]
				team_name = parts[1]
				
				# Update to remove ID
				entry['TEAM'] = team_name
				
				# Add categories if available
				if team_name in team_categories:
					entry['CATEGORIES'] = ', '.join(team_categories[team_name])
				else:
					# Try looking up by team ID
					matching_teams = projects_df[projects_df['BUIDL ID'] == int(team_id)]
					if not matching_teams.empty:
						row = matching_teams.iloc[0]
						categories = []
						
						if pd.notna(row['Track']):
							categories.append(row['Track'])
						
						if pd.notna(row['Bounties']):
							bounties = row['Bounties'].replace('"', '')
							if ',' in bounties:
								bounties_list = [b.strip() for b in bounties.split(',')]
								categories.extend(bounties_list)
							else:
								categories.append(bounties.strip())
						
						mlh_categories = []
						for cat in categories:
							if any(keyword.lower() in cat.lower() for keyword in mlh_keywords):
								mlh_categories.append(cat)
						
						entry['CATEGORIES'] = ', '.join(mlh_categories)
					else:
						entry['CATEGORIES'] = ''
		
		enhanced_schedule.append(entry)
	
	# Determine fieldnames - keep original and add CATEGORIES
	if mlh_schedule:
		fieldnames = list(mlh_schedule[0].keys())
		if 'CATEGORIES' not in fieldnames:
			fieldnames.append('CATEGORIES')
	else:
		fieldnames = ['TIMESLOT', 'TEAM', 'Creativity (/10)', 'Usefulness (/10)',
		              'Presentation (/10)', 'Technical Difficulty (/10)', 'CATEGORIES']
	
	# Write the enhanced schedule
	try:
		with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
			writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
			writer.writeheader()
			writer.writerows(enhanced_schedule)
		
		print(f"Enhanced MLH schedule written to: {output_csv_path}")
	except Exception as e:
		print(f"Error writing enhanced schedule: {e}")

if __name__ == "__main__":
	mlh_schedule_path = "mlh.csv"
	projects_data_path = "buidl_export(8).csv"
	output_path = "Enhanced_MLH_Schedule.csv"
	
	enhance_mlh_schedule(mlh_schedule_path, projects_data_path, output_path)