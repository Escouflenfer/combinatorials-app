import sys

from functions_profil import *

# Change working directory to app.py in order to properly resolve relative file pathing

os.chdir(Path(__file__).parent.parent.parent)

# try:
if __name__ == "__main__":
    # Fetch arguments passed to the script
    hdf5_path = sys.argv[1]
    fit_height = int(sys.argv[2])
    nb_steps = int(sys.argv[3])


    if hdf5_path is not None:
        profil_batch_fit_steps(hdf5_path, fit_height, nb_steps)
    else:
        print("HDF5 path has not been set")
