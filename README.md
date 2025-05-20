# JAMHacks9 Judging Scheduler

This script automates the process of creating and assigning judging timeslots for jamhacks. It takes a CSV file of hackathon projects and their submitted categories, and generates a set of schedules for different judging rooms and categories.

## Features

*   **Automated Timeslot Assignment:** Assigns rooms and times to all participating teams.
*   **Category-Specific Scheduling:** Handles general judging as well as specific sponsor and MLH prize categories.
*   **MLH Category Handling:** Groups MLH prize categories ("Best Use of MongoDB Atlas", "Best GenAI", "Best .Tech Domain Name") to be judged together.
*   **Configurable Judging Durations:** Allows different time durations for general judging versus specific category judging.
*   **Buffer Time:** Includes an 8-minute buffer time between judging slots for a team to prevent back-to-back judging.
*   **Flexible Start and End Times:** Allows specification of a preferred judging window.
*   **CSV Output:** Generates individual CSV files for each judging room/category and a master schedule.

## Prerequisites

*   uv package manager

## Input CSV Format

The script expects an input CSV file (e.g., `buidl_export.csv`) with the following columns:

*   `BUIDL ID`: Unique identifier for the project.
*   `BUIDL name`: Name of the project.
*   `Contact email`: Contact email for the team.
*   `Please list ALL team members' first and last name separated by a comma:`: List of team members.
*   `Track`: The main track the project is submitted to (e.g., "Best Beginner Hack").
*   `Bounties`: A comma-separated list of prize categories/bounties the project is submitted to (e.g., "Best Developer Tool by Warp, MLH || Best Use of Gen AI").

## How to Use

1.  **Prepare your input CSV:** Ensure your CSV file has the required columns and data. You can export it from Dorahacks
2.  **Run the script:**
    Execute the `main.py` script from your terminal. You will need to modify the `main.py` script to change the input file path and desired start/end times.

    ```bash
    python main.py
    ```

3.  **Review the output:**
    The script will create a directory named `judging_schedules` (or as configured) in the same directory as the script. This folder will contain:
    *   Individual CSV files for each judging room and specific prize category (e.g., `Room_2454_judging.csv`, `1st_floor_Ideas_clinic_MLH_judging.csv`).
    *   A `master_schedule.csv` file that consolidates all judging slots.

## Script Configuration (Hardcoded in `main.py`)

The following parameters are currently hardcoded within the `main.py` script and may need to be adjusted directly in the file:

*   **`input_csv_path`**: Path to your input CSV file.
    *   Example: `buidl_export.csv`
*   **`output_dir`**: Directory where the generated schedule CSVs will be saved.
    *   Default: `judging_schedules`
*   **`NONSPONSOR_CATEGORIES`**: List of categories judged during the general judging rounds.
    *   Example: `["Best Beginner Hack", "Best Solo Hack", "Best Female Hack"]`
*   **`mlh_keywords`**: Keywords used to identify MLH-related categories (though specific MLH categories are also hardcoded).
*   **`all_category_names`**: A comprehensive list of all sponsor and MLH prize categories. This list is crucial for setting up the specific judging schedules.
*   **`category_rooms`**: A dictionary defining:
    *   Rooms and duration for 'General' judging.
    *   The specific room and duration for 'MLH' prizes (judged collectively).
    *   Specific rooms, durations, and potential start delays for other sponsor categories.
*   **`mlh_categories`**: A list of the exact names for the MLH prize categories that will be judged together.
*   **`start_time`**: The desired start time for the judging process (format: "HH:MM").
    *   Example: `datetime.strptime("11:05", "%H:%M")`
*   **`target_end_time`**: The preferred end time for judging (format: "HH:MM"). The script will try to fit schedules within this time but may go over if necessary for all teams.
    *   Example: `datetime.strptime("12:15", "%H:%M")`
*   **Buffer Time**: The script uses a default buffer of 8 minutes between a team's judging slots. This is handled in the scheduling logic.
*   **Judging Duration**:
    *   General Judging: 8 minutes (defined in `category_rooms['General']['duration_minutes']`).
    *   MLH & Sponsor Categories: Typically 3 minutes (defined in their respective `category_rooms` entries).

## Output Files

The script generates several CSV files within the specified output directory:

*   **General Judging Room Schedules:** e.g., `General_2nd_floor_Idea's_clinic_schedule.csv`, `General_2464_schedule.csv`, etc.
    *   Columns: `Team ID`, `Team Name`, `Categories`, `Start Time`, `End Time`
*   **MLH Schedule:** e.g., `MLH_schedule.csv` (covers all MLH prizes together)
    *   Columns: `Team ID`, `Team Name`, `MLH Categories`, `Start Time`, `End Time`
*   **Sponsor Category Schedules:** e.g., `Best_Developer_Tool_by_Warp_schedule.csv`
    *   Columns: `Team ID`, `Team Name`, `Category`, `Start Time`, `End Time`
*   **Master Schedule:** `master_schedule.csv` - A consolidated view of all scheduled slots.
    *   Columns: `Room/Category`, `Team ID`, `Team Name`, `Categories/Specific Prize`, `Start Time`, `End Time`

This master schedule is particularly useful for an overall view of the judging day.

## Important Considerations

*   **Category Name Consistency:** Ensure that the category names in your input CSV file exactly match the names defined in `all_category_names` and `NONSPONSOR_CATEGORIES` within the script (after normalization, which strips quotes and spaces).
*   **Room Availability:** The script assumes all defined rooms are available for the entire duration of the judging.


*This scheduling script was originally created for JAMHacks 9 by [Jason Cameron](https://github.com/JasonLovesDoggo/).*
