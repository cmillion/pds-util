import ast
import struct
import pds4_tools
import numpy as np
import pandas as pd
import os
from collections import OrderedDict

def read_label(labelname):
    """ Read a freestanding PDS Data Label (.LBL) into a dict().
    Might not work properly!
    """
    if labelname[-4:] in ['.img','.IMG']:
        print 'Attempting to read label from image file.'
    if not labelname[-4:] in ['.lbl','.LBL']:
        print 'Warning: Possibly incorrect file type: {t}'.format(
                                                            t=labelname[-3:])
    label = {}
    groupname = None

    with open(labelname,'r') as f:
        for line in f:
            if not line.strip():
                continue
            elif line.strip()=='END':
                return label
            elif '/*' in line:
                continue
            elif line.strip()=='END':
                continue
            elif '=' in line:
                keyword_value = line.split('=')
                if len(keyword_value) != 2:
                    print 'Exception case 1: {e}'.format(e=keyword_value)
                    continue
                keyword = keyword_value[0].strip()
                value = keyword_value[1].strip()
                if not value:
                    line = f.next()
                    value = line.strip()
                while '(' in value and not ')' in value:
                    line = f.next()
                    value += line.strip()
                while '"' in value[0] and not '"' in value[-1]:
                    line = f.next()
                    value += line.strip()
                try:
                    # THIS IS PROBABLY GOING WRONG
                    value = ast.literal_eval(value)

                except:
                    if '(' in value[0] and ')' in value[-1]:
                        value = [a.strip() for a in value[1:-1].split(',')]
                if keyword=='GROUP' or keyword=='OBJECT':
                    groupname = value
                    groupdata = {}
                    continue
                if keyword=='END_GROUP' or keyword=='END_OBJECT':
                    label[groupname]=groupdata
                    groupname = None
                    continue
                if groupname:
                    groupdata[keyword]=value
                else:
                    label[keyword]=value
            else:
                print 'Exception case 2: {e}'.format(e=line)

    return label

def read_image(imagename,labelname=None):
    """ This doesn't work properly... don't use it."""
    if not labelname:
        label = read_label(imagename)
    else:
        label = read_label(labelname)
    bits2format = {8:'B',16:'H',32:'I',64:'Q'}
    try:
        bitcode = bits2format[label['IMAGE']['SAMPLE_BITS']]
        print 'Using bit depth: {b} ({n})'.format(
                                    b=bitcode,n=label['IMAGE']['SAMPLE_BITS'])
    except:
        print 'Nonsense bit length: {b}'.format(b=label['IMAGE']['SAMPLE_BITS'])
        raise
    npixels = label['IMAGE']['LINES']*label['IMAGE']['LINE_SAMPLES']
    nbytes = npixels*label['IMAGE']['SAMPLE_BITS']/8
    endiann = '>' if 'MSB' in label['IMAGE']['SAMPLE_TYPE'] else '<'
    '''fmt contained the problem. see note below...'''
    fmt = '{endian}{pixels}{code}'.format(
                                        endian=endiann,pixels=npixels,code=bitcode)
    '''NOTE: The problem of poor image quality was the result of the endian in the
       format() above being set to a fixed value. Now the endian adapts to the
       endian that is native to the image.'''

    with open(imagename,'rb') as f:
        if not labelname:
            f.seek(label['RECORD_BYTES']*(label['^IMAGE']-1))
        unmasked = struct.unpack(fmt,f.read(nbytes))
        #masked = [label['IMAGE']['SAMPLE_BIT_MASK'] & u for u in unmasked]
        return np.array(unmasked).reshape(
                    label['IMAGE']['LINES'],label['IMAGE']['LINE_SAMPLES'])

def read_dat(filename,write_csv=False,quiet=True):
    """ Reads a PDS4 .dat format file, preserving column order and data type,
    except that byte order is switched to native if applicable. The .dat file
    and .xml label must exist in the same directory.
    """
    if filename[-4:]=='.dat':
        filename.replace('.dat','.xml')
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
