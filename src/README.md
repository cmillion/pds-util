### PDS Data Reader

This is a work in progress. Try:

    import pds
    pds.test_io(10) # to download and read the first 10 test data files

To read files individually, the command is:

    pds.read('filename')

Data is output as an object with attributes corresponding to each data type in the file, as well as the file `LABEL`.

Most PDS3/4 and FITS images and labels / headers seem to work right now. All PDS4 data that is readable with pds4_tools should work, because it's just wrapped herein. Label parsing is all handled by PVL, but labels are restructured as `dict` from the PVL object class. One of the design ideas is to only return data as builtin Python types, numpy arrays, or Pandas DataFrames. There are placeholder functions that throw warnings for unsupported data.

The dependencies are:
* numpy
* pandas
* astropy.io
* pvl (which is included in this repo)

