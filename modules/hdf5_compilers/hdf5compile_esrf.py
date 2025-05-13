"""
Functions for XRD parsing (Rigaku SmartLab and ESRF NeXuS)
"""
import io
import h5py
import fabio
from ..hdf5_compilers.hdf5compile_base import *

ESRF_WRITER_VERSION = '0.1 beta'