import pds4_tools
import numpy as np
import pandas as pd
import os
from collections import OrderedDict

def read_dat(filename,write_csv=False,quiet=True):
    """ Reads a PDS4 .dat format file, preserving column order and data type,
    except that byte order is switched to native if applicable. The .dat file
    and .xml label must exist in the same directory.
    """
    if filename[-4:]=='.dat':
        filename = filename.replace('.dat','.xml')
    if filename[-4:]!='.xml':
        raise TypeError('Unknown filetype: {ext}'.format(ext=filename[-4:]))
    structures = pds4_tools.pds4_read(filename,quiet=quiet)
    dat_dict = OrderedDict({})
    for i in range(len(structures[0].fields)):
        name = structures[0].fields[i].meta_data['name']
        dat_dtype = structures[0].fields[i].meta_data['data_type']
        dtype = pds4_tools.reader.data_types.pds_to_numpy_type(dat_dtype)
        data = np.array(structures[0].fields[i],dtype=dtype)
        if ((sys.byteorder=='little' and '>' in str(dtype)) or
            (sys.byteorder=='big' and '<' in str(dtype))):
            data = data.byteswap().newbyteorder()
        dat_dict[name]=data
    dataframe = pd.DataFrame(dat_dict)
    if write_csv:
        dataframe.to_csv(filename.replace('.xml','.csv'),index=False)
    return dataframe

def dat_to_csv(filename):
    """ Converts a PDS4 file to a Comma Separated Value (CSV) file with
    the same base filename. The .dat file and .xml label must exist in
    the same directory.
    """
    _ = read_dat(filename,write_csv=True)
