import pds4_tools
import numpy as np
import pandas as pd
import os
import sys
from collections import OrderedDict
from astropy.io import fits as pyfits

import struct
import pvl
import gzip
import bz2

def filetype(filename):
    """ Attempt to deduce the filetype based on the filename.
    """
    if '.IMG' in filename.upper():
        return 'IMG'
    elif '.FITS' in filename.upper():
        return 'FITS'
    elif '.DAT' in filename.upper():
        return 'DAT'
    else:
        print('Unsupported file format: [...]{end}'.format(
                                            end=filename[-10:]))
        return

def has_attached_label(filename):
    """ Read the first line of a file to decide if it's a label.
    """
    with open(filename,'rb') as f:
        return 'PDS_VERSION_ID' in str(f.readline())

def parse_attached_label(filename):
    """ Parse an attached label of a IMG file.
    """
    # First grab the entries from the label that define how to read the label
    with open(filename, 'r') as f:
        for line in f:
            if 'PDS_VERSION_ID' in line:
                PDS_VERSION_ID = line.strip().split('=')[1]
            if 'RECORD_BYTES' in line:
                RECORD_BYTES = int(line.strip().split('=')[1])
            if 'LABEL_RECORDS' in line:
                LABEL_RECORDS = int(line.strip().split('=')[1])
                break
    # Read the label and then parse it with PVL
    with open(filename,'rb') as f:
        return pvl.load(f.read(RECORD_BYTES*(LABEL_RECORDS)))

def parse_label(filename):
    """ Wraps forking paths for attached and detached PDS3 labels.
    """
    if not has_attached_label(filename):
        try:
            return pvl.load(filename.replace('.IMG','.LBL'))
        except:
            print('Unable to locate file label.')
            raise
    else:
        return parse_attached_label(filename)

def sample_types():
    """ Defines a translation from PDS data types to Python data types.

    TODO: The commented-out types below are technically valid PDS3
        types, but I haven't yet worked out the translation to Python.
    """
    return {
        'MSB_INTEGER': '>h',
        'INTEGER': '>h',
        'MAC_INTEGER': '>h',
        'SUN_INTEGER': '>h',

        'MSB_UNSIGNED_INTEGER': '>B',
        'UNSIGNED_INTEGER': '>B',
        'MAC_UNSIGNED_INTEGER': '>B',
        'SUN_UNSIGNED_INTEGER': '>B',

        'LSB_INTEGER': '<h',
        'PC_INTEGER': '<h',
        'VAX_INTEGER': '<h',

        'LSB_UNSIGNED_INTEGER': '<B',
        'PC_UNSIGNED_INTEGER': '<B',
        'VAX_UNSIGNED_INTEGER': '<B',
    }
#        'IEEE_REAL': '>f',
#        'FLOAT': '>f',
#        'REAL': '>f',
#        'MAC_REAL': '>f',
#        'SUN_REAL': '>f',

#        'IEEE_COMPLEX': '>c',
#        'COMPLEX': '>c',
#        'MAC_COMPLEX': '>c',
#        'SUN_COMPLEX': '>c',

#        'PC_REAL': '<f',
#        'PC_COMPLEX': '<c',

#        'MSB_BIT_STRING': '>S',
#        'LSB_BIT_STRING': '<S',
#        'VAX_BIT_STRING': '<S',

def get_data_types(filename):
    """ Placeholder function for the fact that PDS3 can contain multiple
    types of data (e.g. an image and a header) which are defined by
    'pointers' in the label. This should be dealt with at some point.
    """
    for k in parse_label(filename).keys():
        if k.startswith('^'):
            print(k)

def data_start_byte(label,pointer):
    """ Determine the first byte of the data in an IMG file from its pointer.
    """
    if type(label[pointer]) is int:
        return label['RECORD_BYTES']*(label[pointer]-1)
    elif type(label[pointer]) is list:
        if type(label[pointer][0]) is int:
            print('b')
            return label[pointer][0]
        else:
            return 0
    else:
        print('WTF?',label[pointer])
        raise

def read_img(filename):
    """ Read a PDS IMG formatted file into an array.
    Return the data _and_ the label.
    """
    label = parse_label(filename)
    BYTES_PER_PIXEL = int(label['IMAGE']['SAMPLE_BITS']/8)
    DTYPE = sample_types()[label['IMAGE']['SAMPLE_TYPE']]
    pixels = label['IMAGE']['LINES']*label['IMAGE']['LINE_SAMPLES']*label['IMAGE']['BANDS']
    fmt = '{endian}{pixels}{fmt}'.format(
        endian=DTYPE[0],
        pixels=pixels,
        fmt=DTYPE[-1])
    try: # a little decision tree to seamlessly deal with compression
        if filename.endswith('.gz'):
            f = gzip.open(filename,'rb')
        if filename.endswith('.bz2'):
            f = bz2.BZ2File(filename,'rb')
        else:
            f = open(filename,'rb')
        f.seek(data_start_byte(label,'^IMAGE'))
        img = np.array(struct.unpack(
            fmt,f.read(pixels*BYTES_PER_PIXEL)))
        # Make sure that single-band images are 2-dim arrays.
        if label['IMAGE']['BANDS']==1:
            img = img.reshape(
                    label['IMAGE']['LINES'],
                    label['IMAGE']['LINE_SAMPLES'])
        else:
            img = img.reshape(
                    label['IMAGE']['BANDS'],
                    label['IMAGE']['LINES'],
                    label['IMAGE']['LINE_SAMPLES'])
    finally:
        f.close()
    return img,label

def read_fits(filename, dim=0, quiet=True):
    """ Read a PDS FITS file into an array.
    Return the data _and_ the label.
    """
    hdulist = pyfits.open(filename)
    data = hdulist[dim].data
    header = hdulist[dim].header
    hdulist.close()
    return data,pds4_tools.read(
                    filename.replace('.fits','.xml'),quiet=True).label.to_dict()

def read_dat(filename,write_csv=False,quiet=True):
    """ Reads a PDS4 .dat format file, preserving column order and data type,
    except that byte order is switched to native if applicable. The .dat file
    and .xml label must exist in the same directory.
    Return the data _and_ the label.
    """
    if filename[-4:].lower()=='.dat':
        filename = filename[:-4]+'.xml'
    if filename[-4:].lower()!='.xml':
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
    return dataframe,pds4_tools.read(
                    filename.replace('.dat','.xml'),quiet=True).label.to_dict()

def dat_to_csv(filename):
    """ Converts a PDS4 file to a Comma Separated Value (CSV) file with
    the same base filename. The .dat file and .xml label must exist in
    the same directory.
    """
    _ = read_dat(filename,write_csv=True)
