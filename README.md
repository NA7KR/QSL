
# QRZ Data Fetcher

This project is a Python-based tool to fetch and update callsign data from QRZ.com and store it in a database. The script provides various functionalities such as fetching specific callsigns, processing multiple callsigns from a file, and refreshing the entire database.

## Prerequisites

### 1. Install Python

If Python is not already installed on your system:

- Download and install Python from the [official Python website](https://www.python.org/downloads/).
- During installation, ensure that you check the option to add Python to your system's PATH.
- two settings need to be changed else next.

![2024-11-26 10_05_22-Download Python _ Python org and 7 more pages - Personal - Microsoft​ Edge Beta](https://github.com/user-attachments/assets/603e30f4-ff9f-461f-9be1-fd093670d0d5)

![2024-11-26 10_07_35-Download Python _ Python org and 7 more pages - Personal - Microsoft​ Edge Beta](https://github.com/user-attachments/assets/1c56c9c5-bf25-44f9-a51a-22dc48c39e66)

Windows Key type: CMD ( click on Command prompt)
in the black screen, type: ```python --version```

![2024-11-26 10_19_12-Microsoft Store](https://github.com/user-attachments/assets/be87b9ad-4f4a-4aac-9646-0baf14e1fd2e)

If you see the version as good.

Next type: 
```pip install requests pyodbc```

![2024-11-26 10_29_30-](https://github.com/user-attachments/assets/620bd489-ff92-4d16-987d-d42d3760ed5d)

Keep screen open

### 2. Set Up Your Working Environment

- Create a directory on your system to store the files, e.g., `C:/QSL`.
- Download zip from https://github.com/NA7KR/QSL/archive/refs/heads/main.zip
- Copy folder `C:/QSL`.
- Copy all necessary files into this folder.

### 3. Configure `config.json`

- Locate the file named `config.json.SETUP` in your working directory.
- Rename the file to `config.json`.
- Open `config.json` in a text editor and update it with your QRZ credentials.

Example:
```json
{
    "username": "N0AAA",
    "password": "MyPassword",
    "agent": "QSL",
    "dsn": "QSL",
    "non_update_statuses": ["SK", "SILENT KEY", "DNU-DESTROY", "Active_DIFF_Address"]
    "username": "your_qrz_username",
    "password": "your_qrz_password",
    "agent": "your_agent_string"
}
```

### 4. Determine Python Architecture

Run the following command to check if your Python installation is 32-bit or 64-bit:
```sh
python fetch_qrz_data.py --arch
```

### 5. Run the Appropriate ODBC Setup

Based on the architecture identified in the previous step, run the corresponding ODBC (32-bit or 64-bit) configuration tool.

### 6. Configure ODBC Data Source (DSN)

- Open the ODBC Data Source Administrator tool (select 32-bit or 64-bit based on your Python architecture).
- Add a new Data Source Name (DSN) for Microsoft Access (`accdb`).
- Point this DSN to the Access database file located in your Dropbox (or other specified location).

## Usage

### 1. View QRZ Data

To view the current QRZ data without making any updates, use:
```sh
python fetch_qrz_data.py --refresh --view
```

### 2. Update the Database with New Data

To refresh the database and update it with the latest QRZ data:
```sh
python fetch_qrz_data.py --refresh --update [--debug]
```

- The `--debug` flag is optional and will print detailed debug information.

### 3. Fetch and Update a Specific Callsign

To fetch data for a specific callsign and update the database:
```sh
python fetch_qrz_data.py --callsign CALLSIGN --update [--debug]
```

- Replace `CALLSIGN` with the actual callsign you want to look up.

### 4. Process Multiple Callsigns from a File

To fetch and update data for multiple callsigns listed in a file:
```sh
python fetch_qrz_data.py --file callsigns.txt --update [--debug]
```

- Ensure that `callsigns.txt` contains one callsign per line.

### 5. Interactive Update for Callsign

To run the script and be prompted interactively for a callsign:
```sh
python fetch_qrz_data.py --update
```

- The script will ask you to enter a callsign, which it will then process and update in the database.

## Command-Line Arguments

- `--callsign CALLSIGN`: Lookup a specific callsign and perform the requested action.
- `--file callsigns.txt`: Process multiple callsigns listed in a file.
- `--update`: Update the database with the fetched data.
- `--refresh`: Refresh the entire database by fetching the latest data and comparing it with existing records.
- `--show-raw-xml`: Show the raw XML data fetched from QRZ.com.
- `--debug`: Print detailed debug information during the script's execution.
- `--arch`: Print the Python architecture (32-bit or 64-bit) and exit.
- `--version`: Print the script version and exit.

## Error Handling

The script handles various errors gracefully:

- **Missing Configuration File**: If `config.json` is not found, the script will print an error message and exit.
- **Invalid JSON in Configuration**: If the JSON in `config.json` is malformed, the script will print an error message and exit.
- **Network Errors**: Handles issues with connecting to QRZ.com, such as invalid credentials or network timeouts.
- **Database Connection Issues**: Prints an error message and exits if the script cannot connect to the database.

## Example Usages

### Fetch and Update a Specific Callsign
```sh
python fetch_qrz_data.py --callsign CALLSIGN --update --debug
```

### Fetch and Update Multiple Callsigns from a File
```sh
python fetch_qrz_data.py --file callsigns.txt --update --debug
```

### Refresh the Entire Database
```sh
python fetch_qrz_data.py --refresh --update --debug
```

### Print Python Architecture
```sh
python fetch_qrz_data.py --arch
```

### Print Script Version
```sh
python fetch_qrz_data.py --version
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please fork the repository and create a pull request with your changes.

## Contact

For any issues or questions, please open an issue on GitHub.
