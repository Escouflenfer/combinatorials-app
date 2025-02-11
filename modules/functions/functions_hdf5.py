from pathlib import Path


def detect_measurement(folderpath: Path):
    """
       Scan a folder to determine which type of measurement it is

       Parameters:
           folderpath (pathlib.Path): Path to the folder to scan

       Returns:
           version (str): detected measurement type
       """
    measurement_dict = {
        "moke": [".txt", ".log", ".csv"],
        "edx": [".spx", ".xlsx", ".rtj2"],
        "dektak": [".asc2d", ".csv"],
        "xrd": [".ras", ".raw", ".asc", ".img", ".pdf"],
    }


    if not folderpath.exists() or not folderpath.is_dir():
        print("The directory does not exist or is not a directory.")
        return None

    for measurement_type, file_type in measurement_dict.items():
        ok = True
        for file in folderpath.rglob('[!.]*'): # Expression needed to remove hidden files from consideration
            if file.is_file() and file.suffix.lower() not in file_type:
                print(f"Found {file.suffix.lower()} file at odds with {measurement_type} spec")
                ok = False
                break
            if not ok:
                break
        if ok:
            return measurement_type