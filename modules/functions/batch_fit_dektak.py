import sys
import os

from functions_profil import *

folderpath = None

# Change working directory to app.py in order to properly resolve relative file pathing

os.chdir(Path(__file__).parent.parent.parent)

# try:
if __name__ == "__main__":
    # Fetch arguments passed to the script
    folderpath = sys.argv[1] if len(sys.argv) > 1 else "DefaultArg1"
    print(folderpath)

if folderpath is not None:
    batch_fit(folderpath)
else:
    print("Folder path has not been set")
# except Exception as e:
#     print(f'{e}')
# finally:
#     input('lol')
