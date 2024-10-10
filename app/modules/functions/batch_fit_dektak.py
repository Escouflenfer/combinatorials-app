import sys

from functions_dektak import *

folderpath = None

# try:
if __name__ == "__main__":
    # Fetch arguments passed to the script
    folderpath = sys.argv[1] if len(sys.argv) > 1 else "DefaultArg1"

if folderpath is not None:
    batch_fit(folderpath)
else:
    print('Folder path has not been set')
# except Exception as e:
#     print(f'{e}')
# finally:
#     input('lol')