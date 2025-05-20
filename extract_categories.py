import csv
import io

data = open("./buidl_export(8).csv").read()

csvfile = io.StringIO(data)
reader = csv.reader(csvfile)
header = next(reader) # Skip header row

bounties_index = -1
for i, col_name in enumerate(header):
    if col_name == "Bounties":
        bounties_index = i
        break

sponsor_categories = []
for row in reader:
    if bounties_index != -1 and len(row) > bounties_index:
        bounty_string = row[bounties_index].strip()
        if bounty_string and bounty_string.lower() != 'n/a':
            # Split the bounty string by comma and add each category
            categories = [cat.strip() for cat in bounty_string.split(',')]
            sponsor_categories.extend(categories)

# Remove duplicates and sort
sponsor_categories = sorted(list(set(sponsor_categories)))

print(sponsor_categories)