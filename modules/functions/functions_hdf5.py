from pathlib import Path
import h5py
import xml.etree.ElementTree as et
import pathlib
import h5py
import numpy as np
import re


def detect_measurement(filename_list: list):
    """
       Scan a folder to determine which type of measurement it is

       Parameters:
           filename_list (list): list containing all filenames to parse

       Returns:
           version (str): detected measurement type
       """
    measurement_dict = {
        "MOKE": ["txt", "log", "csv"],
        "EDX": ["spx", "xlsx", "rtj2"],
        "DEKTAK": ["asc2d", "csv"],
        "XRD": ["ras", "raw", "asc", "img", "pdf"],
    }

    for measurement_type, file_type in measurement_dict.items():
        ok = True
        for filename in filename_list:
            if filename.startswith('.'):
                continue
            if filename.split('.')[-1] not in file_type:
                # print(f"Found .{filename.split('.')[-1]} file at odds with {measurement_type} spec")
                ok = False
                break
            if not ok:
                break
        if ok:
            return measurement_type


