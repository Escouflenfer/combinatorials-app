"""
Functions for XRD parsing (Rigaku SmartLab and ESRF NeXuS)
"""
import io
import h5py
import fabio

from ..functions.functions_shared import is_macos_system_file
from ..hdf5_compilers.hdf5compile_base import *

ESRF_WRITER_VERSION = '0.1 beta'


def return_cdte_source_path(dataset_group):
    """
    Return the source path of a virtual dataset (such as Cdte images in NeXuS h5 files)

    @param:
    dataset_group (h5py.Group): dataset group

    @return:
    pathlib.Path: Path to the source file
    """

    if not dataset_group.is_virtual:
        raise TypeError("Given dataset needs to be a virtual dataset")
    # Get the dataset creation property list (DCPL)
    dcpl = dataset_group.id.get_create_plist()

    # Get number of virtual mappings
    num_sources = dcpl.get_virtual_count()

    # Loop through all source mappings
    for i in range(num_sources):
        src_file = dcpl.get_virtual_filename(i)  # Source file (can be '.' if same file)

        src_file_path = Path(src_file.decode() if isinstance(src_file, bytes) else src_file)

        return src_file_path


def esrf_check_if_alignment(hdf5_group):
    """
        Return the source path of a virtual dataset (such as Cdte images in NeXuS h5 files)

        @param:
        dataset_group (h5py.Group): dataset group

        @return:
        Bool: True if the file is an alignment scan, False otherwise
        str: The type of alignment scan, th or tsz. If False, returns None
    """
    title = str(hdf5_group["title"][()])

    if "ascan" in title:
        if "th" in title:
            return True, 'th'
        if "tsz" in title:
            return True, 'tsz'

    return False, None


def get_results_from_refinement(filepath):
    """
    Reads a .lst file and returns the following dictionaries:

    r_coeffs: A dictionary containing the R-factors from the refinement.
    global_params: A dictionary containing the global parameters from the refinement.
    phases: A dictionary containing the parameters for each phase, including the atomic positions.

    Parameters
    ----------
    filepath : str or Path
        The filepath to the .lst file

    Returns
    -------
    tuple
        A tuple containing the r_coeffs, global_params, and phases dictionaries
    """
    attrib_list = [
        "SpacegroupNo=",
        "HermannMauguin=",
        "XrayDensity=",
        "Rphase=",
        "UNIT=",
        "A=",
        "B=",
        "C=",
        "k1=",
        "k2=",
        "B1=",
    ]
    r_coeffs, global_params, phases = {}, {}, {}
    current_phase = "None"

    with open(filepath, 'r') as f:
        lines = f.readlines()

    for idx, line in enumerate(lines):
        # Parse the result file from the refinement
        if line.startswith("Rp="):
            R_factors = line.split()
            for elm in [elm.strip().split("=") for elm in R_factors]:
                r_coeffs[elm[0]] = elm[1]
        elif line.startswith("Q"):
            elm = line.strip().split("=")
            global_params[elm[0]] = elm[1]
        elif line.startswith("Local parameters and GOALs for phase"):
            current_phase = line.split()[-1]
            phases[current_phase] = {}
        elif True in [line.startswith(elm) for elm in attrib_list]:
            elm = line.strip().split("=")
            phases[current_phase][elm[0]] = elm[1]
        elif line.startswith("GEWICHT="):
            elm = [elm.split("=") for elm in line.strip().split(", ")]
            phases[current_phase][elm[0][0]] = elm[0][1]
            # Check if the mean value of GEWICHT was also calculated
            if len(elm) > 1:
                phases[current_phase][elm[1][0]] = float(elm[1][1])
        elif line.startswith("Atomic positions for phase"):
            phases[current_phase]["Atomic positions"] = {}
            atomic_positions = []

            for atomic_position_line in lines[idx:]:
                atomic_positions.append(atomic_position_line)
            phases[current_phase]["Atomic positions"] = atomic_positions

    return r_coeffs, global_params, phases


def write_esrf_to_hdf5(hdf5_path, source_path, dataset_name):
    if isinstance (hdf5_path, str):
        hdf5_path = Path(hdf5_path)
    if isinstance(source_path, str):
        source_path = Path(source_path)

    processed_h5_path = raw_h5_path = None

    if dataset_name is None:
        dataset_name = source_path.stem

    for file in source_path.rglob("*.h5"):
        if "PROCESSED_DATA" in str(file):
            processed_h5_path = file
            raw_h5_path = Path(file.as_posix().replace("PROCESSED_DATA", "RAW_DATA"))

    if processed_h5_path is None:
        raise NameError("Couldn't locate PROCESSED_DATA H5 file")
    if raw_h5_path is None:
        raise NameError("Couldn't locate RAW_DATA H5 file")


    with h5py.File(hdf5_path, 'a') as hdf5_file:
        with h5py.File(raw_h5_path, "r") as raw_source:
            esrf_group = hdf5_file.create_group(dataset_name)
            alignment_group = esrf_group.create_group("alignment_scans")
            for name, group in raw_source.items():
                alignment_test, type = esrf_check_if_alignment(group)

                source_instrument_group = group.get('instrument')
                source_measurement_group = group.get("measurement")

                x_pos = np.round(source_instrument_group["positioners/xsamp"][()])
                y_pos = np.round(source_instrument_group["positioners/ysamp"][()])

                if alignment_test:
                    target_position_group = create_incremental_group(alignment_group, f"{type}_alignment")
                else:
                    target_position_group = esrf_group.create_group(f"({x_pos},{y_pos})")

                target_position_group.attrs["index"] = name

                # Brutal copy of instrument group, it's a dump anyways
                raw_source.copy(source_instrument_group, target_position_group, expand_soft=True)
                rename_group(target_position_group, "instrument/positioners/xsamp", "instrument/x_pos")
                rename_group(target_position_group, "instrument/positioners/ysamp", "instrument/y_pos")

                # Put some basic order in the measurement group
                target_measurement_group = target_position_group.create_group("measurement")
                for subname, subgroup in source_measurement_group.items():
                    if subname == "CdTe":
                        cdte_path = return_cdte_source_path(subgroup)
                        abs_cdte_path = raw_h5_path.parent / cdte_path
                        with h5py.File(abs_cdte_path, "r") as cdte_source:
                            cdte_measurement_group = cdte_source.get("entry_0000/measurement")
                            cdte_measurement_group.copy("data", target_measurement_group, "CdTe")

                    if "CdTe_" in subname:
                        roi_name = subname.split("_")[1]
                        roi_group = safe_create_new_subgroup(target_measurement_group, f"CdTe_roi_{roi_name}")
                        raw_source.copy(subgroup, roi_group)
                    elif "falconx" in subname:
                        falconx_group = safe_create_new_subgroup(target_measurement_group, "falconx")
                        raw_source.copy(subgroup, falconx_group)
                    elif subname in source_instrument_group:
                        continue
                    else:
                        raw_source.copy(subgroup, target_measurement_group)

        with h5py.File(processed_h5_path, "r") as processed_source:
            for name, group in processed_source.items():
                integrate_group = group.get("CdTe_integrate")
                for target_name, target_group in esrf_group.items():
                    if "alignment" in target_name:
                        continue
                    if target_group.attrs["index"] == name:
                        target_position_group = esrf_group.get(target_name)
                        target_instrument_group = target_position_group.get("instrument")
                        processed_source.copy(integrate_group, target_instrument_group)

                        target_measurement_group = target_position_group.get("measurement")
                        target_integrated_group = target_instrument_group.get("CdTe_integrate/integrated")
                        processed_source.copy(target_integrated_group, target_measurement_group, "CdTe_integrate")
                        del target_integrated_group

    return None



def write_xrd_results_to_hdf5(hdf5_path, results_folderpath, target_dataset):
    with h5py.File(hdf5_path, "a") as target:

        if target_dataset not in target:
            raise NameError("Couldn't locate target dataset")

        esrf_group = target.get(target_dataset)
        for lst_filepath in results_folderpath.rglob("*.lst"):
            if is_macos_system_file(lst_filepath):
                continue
            dia_filepath = lst_filepath.with_suffix(".dia")
            file_index = str(lst_filepath.stem).split('_')[-1]
            for name, group in esrf_group.items():
                if name == "alignment_scans":
                    continue
                else:
                    if group.attrs["index"].split('.')[0] == file_index:
                        r_coeffs, global_params, phases = get_results_from_refinement(lst_filepath)

                        column_names = ["Angle", "Total Counts", "Calculated", "Background"] + list(phases)
                        df = pd.read_csv(dia_filepath, sep=r'\s+', engine='python', skiprows=1, header=None,
                                         names=column_names)
                        df["Residual"] = df["Total Counts"] - df["Calculated"]

                        target_results_group = safe_create_new_subgroup(group, "results3")

                        r_coeffs_group = target_results_group.create_group("r_coefficients")
                        write_dict_to_hdf5(r_coeffs, r_coeffs_group)

                        global_parameters_group = target_results_group.create_group("global_parameters")
                        write_dict_to_hdf5(global_params, global_parameters_group)

                        phases_group = target_results_group.create_group("phases")
                        write_dict_to_hdf5(phases, phases_group)

                        fit_group = target_results_group.create_group("fits")
                        for col in df.columns:
                            node = fit_group.create_dataset(col, data=np.array(df[col]), dtype='float')

                        break
