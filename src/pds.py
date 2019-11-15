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

"""
The following three functions are substantially derived from code in
https://github.com/astroML/astroML and so carry the following license:

Copyright (c) 2012-2013, Jacob Vanderplas All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
if sys.version_info[0] == 3:
    from urllib.request import urlopen
    from urllib.error import HTTPError
    from urllib.parse import urlencode
    from io import BytesIO
else:
    from urllib2 import urlopen
    from urllib2 import HTTPError
    from urllib import urlencode
    from cStringIO import StringIO as BytesIO


def url_content_length(fhandle):
    if sys.version_info[0] == 3:
        length = dict(fhandle.info())["Content-Length"]
    else:
        length = fhandle.info().getheader("Content-Length")
    return int(length.strip())


def bytes_to_string(nbytes):
    if nbytes < 1024:
        return "%ib" % nbytes
    nbytes /= 1024.0
    if nbytes < 1024:
        return "%.1fkb" % nbytes
    nbytes /= 1024.0
    if nbytes < 1024:
        return "%.2fMb" % nbytes
    nbytes /= 1024.0
    return "%.1fGb" % nbytes


def download_with_progress_bar(data_url, file_path, force=False, quiet=False):
    if os.path.exists(file_path) and not force:
        if not quiet:
            print("{fn} already exists.".format(fn=file_path.split("/")[-1]))
            print("\t Use `force` to redownload.")
        return 0
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
    num_units = 40
    try:
        fhandle = urlopen(data_url)
    except HTTPError as e:
        # print("***", e)
        # print("\t", data_url)
        return 1
    content_length = url_content_length(fhandle)
    chunk_size = content_length // num_units
    print(
        "Downloading -from- {url}\n\t-to- {cal_dir}".format(
            url=data_url, cal_dir=os.path.dirname(file_path)
        )
    )
    nchunks = 0
    buf = BytesIO()
    content_length_str = bytes_to_string(content_length)
    while True:
        next_chunk = fhandle.read(chunk_size)
        nchunks += 1
        if next_chunk:
            buf.write(next_chunk)
            s = (
                "["
                + nchunks * "="
                + (num_units - 1 - nchunks) * " "
                + "]  %s / %s   \r" % (bytes_to_string(buf.tell()), content_length_str)
            )
        else:
            sys.stdout.write("\n")
            break

        sys.stdout.write(s)
        sys.stdout.flush()

    buf.seek(0)
    open(file_path, "wb").write(buf.getvalue())
    return 0


###
### END code derived from astroML
###


def pvl_to_dict(labeldata):
    # Convert a PVL label object to a Python dict
    data = {}
    if (
        (type(labeldata) == pvl._collections.PVLModule)
        or (type(labeldata) == pvl._collections.PVLGroup)
        or (type(labeldata) == pvl._collections.PVLObject)
    ):
        for k in labeldata.keys():
            data[k] = pvl_to_dict(labeldata[k])
    else:
        return labeldata
    return data


def filetype(filename):
    """ Attempt to deduce the filetype based on the filename.
    """
    if ".IMG" in filename.upper():
        return "IMG"
    elif ".FITS" in filename.upper():
        return "FITS"
    elif ".DAT" in filename.upper():
        if os.path.exists(filename.replace(".DAT", ".LBL")):
            # PDS3 .DAT with detached PVL label
            return "PDS3DAT"
        else:
            # presumed PDS4 .DAT with detached xml label
            return "PDS4DAT"
    else:
        print("*** Unsupported file type: [...]{end}".format(end=filename[-10:]))
        return "UNK"


def has_attached_label(filename):
    """ Read the first line of a file to decide if it's a label.
    """
    with open(filename, "rb") as f:
        return "PDS_VERSION_ID" in str(f.readline())


def parse_attached_label(filename):
    """ Parse an attached label of a IMG file.
    """
    # First grab the entries from the label that define how to read the label
    with open(filename, "rb") as f:
        for line_ in f:
            line = line_.decode("utf-8").strip()  # hacks through a rare error
            if "PDS_VERSION_ID" in line:
                PDS_VERSION_ID = line.strip().split("=")[1]
            if "RECORD_BYTES" in line:
                RECORD_BYTES = int(line.strip().split("=")[1])
            if "LABEL_RECORDS" in line:
                LABEL_RECORDS = int(line.strip().split("=")[1])
                break
    # Read the label and then parse it with PVL
    try:
        with open(filename, "rb") as f:
            return pvl.load(f.read(RECORD_BYTES * (LABEL_RECORDS)))
    except:
        with open(filename, "rb") as f:
            return pvl.load(f.read(RECORD_BYTES * (LABEL_RECORDS)), strict=False)


def parse_label(filename):
    """ Wraps forking paths for attached and detached PDS3 labels.
    """
    if not has_attached_label(filename):
        if os.path.exists(filename[: filename.rfind(".")] + ".LBL"):
            return pvl_to_dict(pvl.load(filename[: filename.rfind(".")] + ".LBL"))
        elif os.path.exists(filename[: filename.rfind(".")] + ".lbl"):
            return pvl_to_dict(pvl.load(filename[: filename.rfind(".")] + ".lbl"))
        elif os.path.exists(filename[: filename.rfind(".")] + ".xml"):
            return pds4_tools.read(
                filename[: filename.rfind(".")] + ".xml", quiet=True
            ).label.to_dict()
        else:
            print("Unable to locate file label.")
            return None
    else:
        return parse_attached_label(filename)


def sample_types():
    """ Defines a translation from PDS data types to Python data types.

    TODO: The commented-out types below are technically valid PDS3
        types, but I haven't yet worked out the translation to Python.
    """
    return {
        "MSB_INTEGER": ">h",
        "INTEGER": ">h",
        "MAC_INTEGER": ">h",
        "SUN_INTEGER": ">h",
        "MSB_UNSIGNED_INTEGER": ">B",
        "UNSIGNED_INTEGER": ">B",
        "MAC_UNSIGNED_INTEGER": ">B",
        "SUN_UNSIGNED_INTEGER": ">B",
        "LSB_INTEGER": "<h",
        "PC_INTEGER": "<h",
        "VAX_INTEGER": "<h",
        "LSB_UNSIGNED_INTEGER": "<B",
        "PC_UNSIGNED_INTEGER": "<B",
        "VAX_UNSIGNED_INTEGER": "<B",
        "IEEE_REAL": ">f",
        "PC_REAL": "<f",
        "FLOAT": ">f",
        "REAL": ">f",
        "MAC_REAL": ">f",
        "SUN_REAL": ">f",
    }


#        'IEEE_COMPLEX': '>c',
#        'COMPLEX': '>c',
#        'MAC_COMPLEX': '>c',
#        'SUN_COMPLEX': '>c',

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
        if k.startswith("^"):
            print(k)


def data_start_byte(label, pointer):
    """ Determine the first byte of the data in an IMG file from its pointer.
    """
    if type(label[pointer]) is int:
        return label["RECORD_BYTES"] * (label[pointer] - 1)
    elif type(label[pointer]) is list:
        if type(label[pointer][0]) is int:
            return label[pointer][0]
        elif type(label[pointer][-1]) is int:
            return label["RECORD_BYTES"] * (label[pointer][-1] - 1)
        else:
            return 0
    elif type(label[pointer]) is str:
        return 0
    else:
        print("WTF?", label[pointer])
        raise


def read_image(filename):  # ^IMAGE
    """ Read a PDS IMG formatted file into an array.
    TODO: Check for and account for LINE_PREFIX.
    TODO: Check for and apply BIT_MASK.
    """
    label = parse_label(filename)
    if "IMAGE" in label.keys():
        BYTES_PER_PIXEL = int(label["IMAGE"]["SAMPLE_BITS"] / 8)
        DTYPE = sample_types()[label["IMAGE"]["SAMPLE_TYPE"]]
        nrows = label["IMAGE"]["LINES"]
        ncols = label["IMAGE"]["LINE_SAMPLES"]
        try:
            BANDS = label["IMAGE"]["BANDS"]
        except KeyError:
            BANDS = 1
        pixels = nrows * ncols * BANDS
    else:
        print("*** IMG w/ old format attached label not currently supported.")
        print("\t{fn}".format(fn=filename))
        return None, None
    fmt = "{endian}{pixels}{fmt}".format(endian=DTYPE[0], pixels=pixels, fmt=DTYPE[-1])
    try:  # a little decision tree to seamlessly deal with compression
        if filename.endswith(".gz"):
            f = gzip.open(filename, "rb")
        if filename.endswith(".bz2"):
            f = bz2.BZ2File(filename, "rb")
        else:
            f = open(filename, "rb")
        f.seek(data_start_byte(label, "^IMAGE"))
        image = np.array(struct.unpack(fmt, f.read(pixels * BYTES_PER_PIXEL)))
        # Make sure that single-band images are 2-dim arrays.
        if BANDS == 1:
            image = image.reshape(nrows, ncols)
        else:
            image = image.reshape(BANDS, nrows, ncols)
    finally:
        f.close()
    # if len(np.shape(image))==2:
    #    plt.figure(figsize=(10,10))
    #    plt.title(filename.split('/')[-1])
    #    plt.imshow(image,cmap='gray')
    return image


def read_image_header(filename):  # ^IMAGE_HEADER
    label = parse_label(filename)
    try:
        with open(filename, "rb") as f:
            f.seek(data_start_byte(label, "^IMAGE_HEADER"))
            image_header = pvl_to_dict(pvl.load(f.read(label["IMAGE_HEADER"]["BYTES"])))
        return image_header
    except:
        print("Unable to parse image header.")
        return


def read_telemetry_table(filename):  # ^TELEMETRY_TABLE
    label = parse_label(filename)
    with open(filename, "rb") as f:
        f.seek(data_start_byte(label, "^TELEMETRY_TABLE"))
        telemetry_table = f.read(
            label["TELEMETRY_TABLE"]["ROWS"]
            * label["TELEMETRY_TABLE"]["COLUMNS"]
            * label["TELEMETRY_TABLE"]["ROW_BYTES"]
        )
    print(
        "TELEMETRY_TABLE not parsable without file: {STRUCTURE}".format(
            STRUCTURE=label["TELEMETRY_TABLE"]["^STRUCTURE"]
        )
    )
    return telemetry_table


def read_bad_data_values_header(filename):  # ^BAD_DATA_VALUES_HEADER
    label = parse_label(filename)
    with open(filename, "rb") as f:
        f.seek(data_start_byte(label, "^BAD_DATA_VALUES_HEADER"))
        bad_data_values_header = f.read(label["BAD_DATA_VALUES_HEADER"]["BYTES"])
    print(
        "BAD_DATA_VALUES_HEADER not parsable without file: {DESCRIPTION}".format(
            DESCRIPTION=label["BAD_DATA_VALUES_HEADER"]["^DESCRIPTION"]
        )
    )
    return bad_data_values_header


def read_line_prefix_table(filename):
    print("LINE_PREFIX_TABLE is TBD.")
    return


def read_histogram(filename):
    label = parse_label(filename)
    DTYPE = sample_types()[label["HISTOGRAM"]["DATA_TYPE"]]
    if label["HISTOGRAM"]["ITEM_BYTES"] == 4:
        DTYPE = DTYPE[0] + "i"  # because why would the type
        # definitions be consistent?
    items = label["HISTOGRAM"]["ITEMS"]
    with open(filename, "rb") as f:
        fmt = "{endian}{items}{fmt}".format(endian=DTYPE[0], items=items, fmt=DTYPE[-1])
        f.seek(data_start_byte(label, "^HISTOGRAM"))
        histogram = np.array(
            struct.unpack(fmt, f.read(items * label["HISTOGRAM"]["ITEM_BYTES"]))
        )
    return histogram


def read_table(filename):
    print("Table data not yet supported.")
    return


def read_engineering_table(filename):
    return read_table(filename)


def read_measurement_table(filename):
    return read_table(filename)


def read_mslmmm_compressed(filename):
    """ WARNING: Placeholder functionality.
    This will run `dat2img` to decompress the file from Malin's bespoke
    image compression format (which has no obvious purpose other than
    obfuscation) into the local direction, then read the resulting file,
    and then delete it.
    TODO: Modify dat2img.c and pdecom_msl.c
    """
    #_ = os.system('./MMM_DAT2IMG/dat2img {fn}'.format(fn=filename))
    print("Do not yet support Malin's bespoke compressed format.")


def read_fits(filename, dim=0, quiet=True):
    """ Read a PDS FITS file into an array.
    Return the data _and_ the label.
    """
    hdulist = pyfits.open(filename)
    data = hdulist[dim].data
    header = hdulist[dim].header
    hdulist.close()
    return (
        data,
        pds4_tools.read(filename.replace(".fits", ".xml"), quiet=True).label.to_dict(),
    )


def read_dat_pds4(filename, write_csv=False, quiet=True):
    """ Reads a PDS4 .dat format file, preserving column order and data type,
    except that byte order is switched to native if applicable. The .dat file
    and .xml label must exist in the same directory.
    Return the data _and_ the label.
    """
    if filename[-4:].lower() == ".dat":
        filename = filename[:-4] + ".xml"
    if filename[-4:].lower() != ".xml":
        raise TypeError("Unknown filetype: {ext}".format(ext=filename[-4:]))
    structures = pds4_tools.pds4_read(filename, quiet=quiet)
    dat_dict = OrderedDict({})
    for i in range(len(structures[0].fields)):
        name = structures[0].fields[i].meta_data["name"]
        dat_dtype = structures[0].fields[i].meta_data["data_type"]
        dtype = pds4_tools.reader.data_types.pds_to_numpy_type(dat_dtype)
        data = np.array(structures[0].fields[i], dtype=dtype)
        if (sys.byteorder == "little" and ">" in str(dtype)) or (
            sys.byteorder == "big" and "<" in str(dtype)
        ):
            data = data.byteswap().newbyteorder()
        dat_dict[name] = data
    dataframe = pd.DataFrame(dat_dict)
    if write_csv:
        dataframe.to_csv(filename.replace(".xml", ".csv"), index=False)
    return dataframe


def read_dat_pds3(filename):
    if not has_attached_label(filename):
        print("*** DAT w/ detached PDS3 LBL not currently supported.")
        try:
            et = parse_label(filename)["COMPRESSED_FILE"]["ENCODING_TYPE"]
            print("\tENCODING_TYPE = {et}".format(et=et))
        except:
            pass
    else:
        print("*** DAT w/ attached PDS3 LBL not current supported.")
    print("\t{fn}".format(fn=filename))
    return None, None


def dat_to_csv(filename):
    """ Converts a PDS4 file to a Comma Separated Value (CSV) file with
    the same base filename. The .dat file and .xml label must exist in
    the same directory.
    """
    _ = read_dat(filename, write_csv=True)


def unknown(filename):
    print("\t{fn}".format(fn=filename))
    return None, None


# def read_any_file(filename):
class data:
    def __init__(self, filename):
        pointer_to_function = {
            "^IMAGE": read_image,
            "^IMAGE_HEADER": read_image_header,
            "^TELEMETRY_TABLE": read_telemetry_table,
            "^BAD_DATA_VALUES_HEADER": read_bad_data_values_header,
            "^LINE_PREFIX_TABLE": read_line_prefix_table,
            "^HISTOGRAM": read_histogram,
            "^MEASUREMENT_TABLE": read_measurement_table,
            "^ENGINEERING_TABLE": read_engineering_table,
            "MSLMMM-COMPRESSED": read_mslmmm_compressed,
        }

        # Try PDS4 options
        if os.path.exists(filename[: filename.rfind(".")] + ".xml"):
            if filename.endswith(".dat"):
                self.dat = read_dat_pds4(filename)
                self.label = pds4_tools.read(
                    filename.replace(".dat", ".xml")
                ).label.to_dict()
                # print('DAT_PDS4',type(data))
        else:
            # Try PDS3 options
            label = parse_label(filename)
            try:
                pointers = [k for k in label.keys() if k[0] is "^"]
            except AttributeError:
                return
            try:
                if label["COMPRESSED_FILE"]["ENCODING_TYPE"] == "MSLMMM-COMPRESSED":
                    pointers += [label["COMPRESSED_FILE"]["ENCODING_TYPE"]]
            except:
                pass
            setattr(self,'LABEL',label)
            print(filename)
            if len(pointers):
                print("\t", pointers)
                for pointer in pointers:
                    try:
                        setattr(
                            self,
                            pointer[1:] if pointer.startswith("^") else pointer,
                            pointer_to_function[pointer](filename),
                        )
                    except KeyError:
                        pass
            else:
                print("\t*** No pointers. ***")


class read:
    def __init__(self, filename):
        self.filename = filename
        self.data = data(filename)


class io:
    def __init__(cls):
        pass

    def read(filename):
        return read(filename)


def url_to_path(url, testdir="../src/test"):
    dirstart = url.split("://")[1].find("/")
    filename = testdir + url.split("://")[1][dirstart:]
    return filename


def download_data_and_label(url):
    filename = url_to_path(url)
    if download_with_progress_bar(url, filename, quiet=True):
        print("An error has occurred: {fn}".format(fn=filename))
        return 1
    for ext in [".LBL", ".lbl", ".xml", ".XML"]:
        if not download_with_progress_bar(
            url[: url.rfind(".")] + ext,
            filename[: filename.rfind(".")] + ext,
            quiet=True,
        ):
            break
    return 0


def download_test_data(
    ndata,
    testdir="../src/test",
    refdatafile="refdata.csv",
):
    refdata = pd.read_csv(refdatafile, comment="#")
    for i, url in enumerate(refdata["url"][:ndata]):
        _ = download_data_and_label(url)
    return


def test_io(
    ndata,
    testdir="../src/test",
    refdata=pd.read_csv("refdata.csv", comment="#"),
):
    for i, url in enumerate(refdata["url"][:ndata]):
        filename = url_to_path(url)
        read(filename)
