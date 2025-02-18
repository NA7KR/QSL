import json  # To handle JSON files
import argparse  # To parse command-line arguments
import requests  # To make HTTP requests
import sys  # To handle system-level operations
import platform  # To retrieve information about the system
import csv  # To handle CSV file operations
import re  # To work with regular expressions
from datetime import datetime  # To work with dates and times

# Attempt to import the 'pyodbc' module, which is required for database connections
try:
    import pyodbc
except ModuleNotFoundError:
    # If 'pyodbc' is not installed, provide a message to the user and exit the program
    print("Error: The 'pyodbc' module is not installed. Please install it using:")
    print("       pip install pyodbc")
    sys.exit(1)  # Exit the program with a status code indicating an error

# Define the script's version number
VERSION = "1.0.6"

def load_config():
    """Load the configuration from the 'config.json' file."""
    try:
        # Attempt to open and load the configuration file
        with open('config.json') as config_file:
            return json.load(config_file)  # Parse the JSON data
    except FileNotFoundError:
        # Handle the case where the configuration file is not found
        print("Error: 'config.json' file not found. Please ensure it is present in the current directory.")
        sys.exit(1)
    except json.JSONDecodeError:
        # Handle the case where the JSON data is malformed
        print("Error: 'config.json' contains invalid JSON. Please check the file format.")
        sys.exit(1)

# Load the configuration into a global variable
config = load_config()
# Load specific configuration values with default fallbacks
NON_UPDATE_STATUSES = config.get('non_update_statuses', ['SK', 'SILENT KEY'])
DSN = config.get('dsn', 'QSL')

class Callsign:
    """A class to represent a radio callsign and its associated data."""
    def __init__(self, call, xref, first_name, last_name, address, town, state, zip_code, country, license_start, license_end, license_class, email, status='Active'):
        self.call = call
        self.xref = xref
        self.first_name = first_name
        self.last_name = last_name
        self.address = address
        self.town = town
        self.state = state
        self.zip_code = zip_code
        self.country = country
        self.license_start = license_start
        self.license_end = license_end
        self.license_class = license_class
        self.email = email
        self.status = status

def get_qrz_session_key(username, password, agent):
    """Retrieve the session key from QRZ.com for API access."""
    url = f'https://xmldata.qrz.com/xml/current/?username={username};password={password};agent={agent}'
    response = requests.get(url)  # Perform the HTTP GET request
    response.raise_for_status()  # Raise an exception if the request failed
    xml_data = response.text  # Retrieve the XML response as a string

    # Check for an error in the XML response
    if '<Error>' in xml_data:
        error_message = extract_xml_value(xml_data, 'Error')
        raise Exception(f'Error: {error_message}')  # Raise an exception with the error message

    # Extract and return the session key from the XML response
    return extract_xml_value(xml_data, 'Key')

def extract_xml_value(xml_data, field):
    """Extract the value of a specific field from the XML data."""
    start = xml_data.find(f'<{field}>') + len(f'<{field}>')
    end = xml_data.find(f'</{field}>')
    # Return the extracted value or None if the field is not found
    return xml_data[start:end] if start != -1 and end != -1 else None

def get_callsign_data(session_key, callsign):
    """Fetch data for a specific callsign from QRZ.com using the session key."""
    url = f'https://xmldata.qrz.com/xml/current/?s={session_key};callsign={callsign}'
    response = requests.get(url)  # Perform the HTTP GET request
    response.raise_for_status()  # Raise an exception if the request failed
    xml_data = response.text  # Retrieve the XML response as a string

    # Check for an error in the XML response
    if '<Error>' in xml_data:
        error_message = extract_xml_value(xml_data, 'Error')
        raise Exception(f'Error: {error_message}')  # Raise an exception with the error message

    # Return the XML data for further processing
    return xml_data

def normalize_first_name(name):
    """
    Normalize a first name by trimming extra spaces, converting to title case,
    and if the name starts with a single letter followed by a space,
    remove that initial letter and the space.
    """
    # Remove extra spaces and convert to title case
    name = " ".join(name.split()).title()
    parts = name.split(" ")
    # If there is more than one word and the first word is a single letter, remove it.
    if len(parts) > 1 and len(parts[0]) == 1:
        return " ".join(parts[1:])
    return name


def parse_callsign_data(xml_data):
    """Parse the XML data into a Callsign object."""
    call = extract_xml_value(xml_data, 'call')
    xref = extract_xml_value(xml_data, 'xref')

    first_name = extract_xml_value(xml_data, 'fname')
    last_name = extract_xml_value(xml_data, 'name')
    
    # Remove any comma and everything after it from the last name
    if last_name:
        last_name = last_name.split(',')[0].strip()
    
    # If the first name is not provided, split the last name into first and last.
    if not first_name:
        name_parts = last_name.split(' ')
        first_name = name_parts[0]
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else name_parts[0]
    else:
        # Convert both names to title case
        first_name = first_name.title()
        last_name = last_name.title()

        # For first name: always keep the first word, but ignore additional words if they are a single letter.
        words = first_name.split()
        if words:
            first_name = " ".join([words[0]] + [w for w in words[1:] if len(w) > 1])
    
    addr1 = extract_xml_value(xml_data, 'addr1')
    town = extract_xml_value(xml_data, 'addr2')
    state = extract_xml_value(xml_data, 'state')
    zip_code = extract_xml_value(xml_data, 'zip')
    country = extract_xml_value(xml_data, 'country')
    license_start = extract_xml_value(xml_data, 'efdate')
    if license_start:
        license_start = license_start.split(' ')[0]
    license_end = extract_xml_value(xml_data, 'expdate')
    if license_end:
        license_end = license_end.split(' ')[0]
    license_class_code = extract_xml_value(xml_data, 'class')
    license_class = map_license_class(license_class_code)
    email = extract_xml_value(xml_data, 'email')

    return Callsign(call, xref, first_name, last_name, addr1, town, state, zip_code, country, license_start, license_end, license_class, email)


def map_license_class(class_code):
    """Map a license class code to its full description."""
    class_map = {
        'E': 'Extra',
        'G': 'General',
        'T': 'Technician',
        'A': 'Advanced',
        'C': 'Club'
    }
    # Return the mapped license class or 'Unknown Class' if the code is not recognized
    return class_map.get(class_code, 'Unknown Class')

def normalize_name(name):
    """Normalize a name by trimming extra spaces and extracting the first word."""
    return ' '.join(name.split()).split(' ')[0]

def process_callsign(session_key, callsign, update, checkstatus, debug, mismatch_log, status_file):
    # Remove '/SK' suffix with digits if present.
    # This will convert, for example, 'KB7OUU/SK2025' to 'KB7OUU'
    cleaned_callsign = re.sub(r'/SK\d+', '', callsign.upper())
    
    try:
        # Fetch the data for the cleaned callsign
        callsign_data = get_callsign_data(session_key, cleaned_callsign)
        # Parse the fetched data into a Callsign object
        parsed_data = parse_callsign_data(callsign_data)
        
        # Update the callsign attribute with the cleaned version
        parsed_data.call = cleaned_callsign
        
        if debug:
            print(f"Fetched data for {cleaned_callsign}: {vars(parsed_data)}")
        if checkstatus:
            check_callsign_status(cleaned_callsign, parsed_data, update, debug, mismatch_log, status_file)
        if update:
            insert_or_update_callsign_in_db(parsed_data, debug, mismatch_log)
    except Exception as e:
        if "Not found" in str(e):
            update_callsign_status_to_inactive_if_needed(cleaned_callsign, debug)
        else:
            print(f'Error fetching data for {cleaned_callsign}: {e}')

def insert_or_update_callsign_in_db(callsign, debug, mismatch_log):
    """Insert or update the callsign data in the database."""
    conn = None
    try:
        conn = pyodbc.connect(f'DSN={DSN}')  # Establish a database connection
        cursor = conn.cursor()  # Create a cursor to execute SQL queries

        try:
            # Attempt to parse the license end date and determine the status based on it
            license_end_date = datetime.strptime(callsign.license_end, '%Y-%m-%d')
            status = "License Expired" if license_end_date < datetime.now() else callsign.status
        except (ValueError, TypeError):
            # Ignore invalid license end dates and do not output an error message
            return

        # Check if the callsign already exists in the database
        cursor.execute("SELECT FirstName, LastName, Status FROM tbl_Operator WHERE Call=?", (callsign.call,))
        row = cursor.fetchone()

        # Get today's date as a string
        today_date = datetime.now().strftime('%Y-%m-%d')

        if row:
            # If the callsign exists, check if the first and last names match
            db_first_name = row[0].rstrip(',')  # Remove trailing comma if exists
            db_last_name = row[1]
            db_status = row[2]

            if normalize_first_name(db_first_name) == normalize_first_name(callsign.first_name) and db_last_name.lower() == callsign.last_name.lower():
            # Proceed with update

                if db_status not in NON_UPDATE_STATUSES:
                    # Update the existing record if the status allows it
                    sql = """
                        UPDATE tbl_Operator SET 
                            FirstName=?, LastName=?, Address_1=?, City=?, State=?, Zip=?, 
                            [Lic-issued]=?, [Lic-exp]=?, [Class]=?, [E-Mail]=?, [Status]=?, [Updated]=?
                        WHERE Call=?
                    """
                    params = (callsign.first_name, callsign.last_name, callsign.address, callsign.town, 
                              callsign.state, callsign.zip_code, callsign.license_start, 
                              callsign.license_end, callsign.license_class, callsign.email, status, today_date, callsign.call)
                    if debug:
                        print(f"Executing SQL: {sql}")
                        print(f"Parameters: {params}")
                    cursor.execute(sql, params)
                    if debug:
                        print(f"Updated {callsign.call} in the database.")
            else:
                # Log and report a mismatch if the names do not match
                mismatch_message = f"No update performed for callsign {callsign.call} due to mismatch in first or last name.\n"
                if normalize_name(db_first_name.lower()) != normalize_name(callsign.first_name.lower()):
                    mismatch_message += f"First name mismatch: DB = {db_first_name}, QRZ = {callsign.first_name}\n"
                if db_last_name.lower() != callsign.last_name.lower():
                    mismatch_message += f"Last name mismatch: DB = {db_last_name}, QRZ = {callsign.last_name}\n"
                print(mismatch_message)
                with open(mismatch_log, 'a') as file:
                    file.write(mismatch_message)
        else:
            # Insert a new record if the callsign does not exist in the database
            status = "New"
            sql = """
                INSERT INTO tbl_Operator (Call, FirstName, LastName, Address_1, City, State, Zip, [Lic-issued], [Lic-exp], [Class], [E-Mail], [Status], [Updated])
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (callsign.call, callsign.first_name, callsign.last_name, callsign.address, callsign.town, 
                      callsign.state, callsign.zip_code, callsign.license_start, 
                      callsign.license_end, callsign.license_class, callsign.email, status, today_date)
            if debug:
                print(f"Executing SQL: {sql}")
                print(f"Parameters: {params}")
            cursor.execute(sql, params)
            if debug:
                print(f"Inserted {callsign.call} into the database.")
        
        conn.commit()  # Commit the transaction to the database
    except pyodbc.Error as e:
        # Include the callsign in the error message
        print(f'Error inserting or updating callsign {callsign.call} in database: {e}')
    finally:
        if conn:
            conn.close()  # Close the database connection

def update_callsign_status_to_inactive_if_needed(callsign, debug):
    """Update the status of a callsign to 'Inactive' if necessary."""
    conn = None
    try:
        conn = pyodbc.connect(f'DSN={DSN}')  # Establish a database connection
        cursor = conn.cursor()  # Create a cursor to execute SQL queries
        cursor.execute("SELECT [Status] FROM tbl_Operator WHERE Call=?", (callsign,))
        row = cursor.fetchone()
        if row and row[0] not in NON_UPDATE_STATUSES:
            # Update the status to 'Inactive' if the current status allows it
            sql = "UPDATE tbl_Operator SET [Status]='Inactive', [Updated]=? WHERE Call=?"
            params = (datetime.now().strftime('%Y-%m-%d'), callsign)
            if debug:
                # Output the SQL query and parameters if debugging is enabled
                print(f"Executing SQL: {sql}")
                print(f"Parameters: {params}")
            cursor.execute(sql, params)
            conn.commit()  # Commit the transaction to the database
            if debug:
                # Confirm the update if debugging is enabled
                print(f"Callsign {callsign} status updated to Inactive.")
    except pyodbc.Error as e:
        # Handle database errors and output an error message
        print(f'Error updating callsign status in database: {e}')
    finally:
        if conn:
            conn.close()  # Close the database connection

def check_callsign_status(callsign, parsed_data, update, debug, mismatch_log, status_file):
    """Check the current status of a callsign in the database and log any discrepancies."""
    conn = None
    try:
        conn = pyodbc.connect(f'DSN={DSN}')  # Establish a database connection
        cursor = conn.cursor()  # Create a cursor to execute SQL queries
        cursor.execute("SELECT [Status] FROM tbl_Operator WHERE Call=?", (callsign,))
        row = cursor.fetchone()
        if row:
            db_status = row[0]
            # Determine the expected status based on the license end date
            expected_status = "License Expired" if datetime.strptime(parsed_data.license_end, '%Y-%m-%d') < datetime.now() else "Active"
            if db_status != expected_status:
                # Log the discrepancy to a status file
                with open(status_file, 'a') as file:
                    file.write(f"{callsign}: Expected status {expected_status}, found {db_status}\n")
                if debug:
                    # Output the discrepancy if debugging is enabled
                    print(f"{callsign}: Expected status {expected_status}, found {db_status}")
                if update and db_status not in NON_UPDATE_STATUSES:
                    # Update the database if necessary
                    insert_or_update_callsign_in_db(parsed_data, debug, mismatch_log)
    except pyodbc.Error as e:
        # Handle database errors and output an error message
        print(f'Error checking callsign status in database: {e}')
    finally:
        if conn:
            conn.close()  # Close the database connection

def refresh_database(update, checkstatus, debug, mismatch_log, status_file):
    """Refresh the entire database by processing all callsigns in the database."""
    conn = None
    try:
        # Retrieve the session key from QRZ.com
        session_key = get_qrz_session_key(config['username'], config['password'], config['agent'])
        conn = pyodbc.connect(f'DSN={DSN}')  # Establish a database connection
        cursor = conn.cursor()  # Create a cursor to execute SQL queries
        
        # Retrieve all callsigns from the database
        cursor.execute("SELECT Call FROM tbl_Operator")
        callsigns = [row[0] for row in cursor.fetchall()]
        
        if debug:
            # Output the total number of records to process if debugging is enabled
            print(f"Total records to process: {len(callsigns)}")
        
        # Process each callsign individually
        for call in callsigns:
            process_callsign(session_key, call, update, checkstatus, debug, mismatch_log, status_file)

    except pyodbc.Error as e:
        # Handle database errors and output an error message
        print(f'Error refreshing database: {e}')
    finally:
        if conn:
            conn.close()  # Close the database connection

def export_to_csv(filename):
    """Export the database to a CSV file."""
    conn = None
    try:
        conn = pyodbc.connect(f'DSN={DSN}')  # Establish a database connection
        cursor = conn.cursor()  # Create a cursor to execute SQL queries
        
        # Retrieve all records from the database
        cursor.execute("SELECT * FROM tbl_Operator")
        columns = [column[0] for column in cursor.description]  # Extract column names
        rows = cursor.fetchall()  # Fetch all data rows

        # Write the data to a CSV file
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(columns)  # Write the header row
            writer.writerows(rows)  # Write the data rows
        
        print(f"Database exported to {filename}")
    except pyodbc.Error as e:
        # Handle database errors and output an error message
        print(f'Error exporting database to CSV: {e}')
    finally:
        if conn:
            conn.close()  # Close the database connection

def main():
    """Main entry point of the script."""
    parser = argparse.ArgumentParser(description='Fetch QRZ Callsign Data')
    # Define command-line arguments and options
    parser.add_argument('--callsign', type=str, help='The callsign to lookup')
    parser.add_argument('--file', type=str, help='File containing callsigns, one per line')
    parser.add_argument('--update', action='store_true', help='Update the database with fetched data')
    parser.add_argument('--refresh', action='store_true', help='Refresh the database to check and correct data formatting')
    parser.add_argument('--checkstatus', action='store_true', help='Check the status of callsigns and log discrepancies')
    parser.add_argument('--export', type=str, help='Export the database to a CSV file')
    parser.add_argument('--debug', action='store_true', help='Show debug information')
    parser.add_argument('--arch', action='store_true', help='Print the Python architecture and exit')
    parser.add_argument('--version', action='store_true', help='Print the script version and exit')
    args = parser.parse_args()  # Parse the command-line arguments

    # Handle the '--arch' option to print the Python architecture and exit
    if args.arch:
        print(platform.architecture())
        sys.exit(0)

    # Handle the '--version' option to print the script version and exit
    if args.version:
        print(f"Script Version: {VERSION}")
        
        sys.exit(0)

    # Define filenames for logging mismatches and status discrepancies
    mismatch_log = f"Mismatch-{datetime.now().strftime('%Y-%m-%d')}.txt"
    status_file = f"status-{datetime.now().strftime('%Y-%m-%d')}.txt"

    try:
        # Retrieve the session key from QRZ.com
        session_key = get_qrz_session_key(config['username'], config['password'], config['agent'])

        # Handle the '--export' option to export the database to a CSV file
        if args.export:
            export_to_csv(args.export)
        # Handle the '--refresh' option or the case where no specific callsign or file is provided
        elif args.refresh or (not args.callsign and not args.file):
            refresh_database(args.update, args.checkstatus, args.debug, mismatch_log, status_file)
        # Handle the '--file' option to process callsigns from a file
        elif args.file:
            with open(args.file, 'r') as file:
                callsigns = file.readlines()
            callsigns = [callsign.strip().upper() for callsign in callsigns if callsign.strip()]
            for callsign in callsigns:
                process_callsign(session_key, callsign, args.update, args.checkstatus, args.debug, mismatch_log, status_file)
        # Handle the '--callsign' option to process a single callsign
        elif args.callsign:
            process_callsign(session_key, args.callsign.upper(), args.update, args.checkstatus, args.debug, mismatch_log, status_file)

    except requests.exceptions.RequestException as e:
        # Handle network-related errors
        print(f'Network error: {e}')
    except pyodbc.Error as e:
        # Handle database connection errors
        print(f'Database connection error: {e}')
    except Exception as e:
        # Handle all other exceptions and output an error message
        print(f'Error: {e}')

# Ensure the script runs only when executed directly
if __name__ == '__main__':
    main()
