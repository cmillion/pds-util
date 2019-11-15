# pds-util
Command line utilities and examples for working with Planetary Data System (PDS) data in Python.

### Universal PDS Data Read (prototype)
The basic idea is to have a single function call (e.g. `read(filename)`) that will parse any type of observational data contained in the PDS archives and return it in easy Python data structures. Part of the philosophy is that the only allowed data structures in output are: Python built-ins, numpy arrays, and Pandas DataFrames. The data are actually attributes of a returned object that also contains the filepath, metadata, etc. Some PDS data files contain more than one data type, so each of these gets its own attribute. It seems to work about 70% for image data right now, and on a handful of other data types. It might completely work for PDS4 data, because it just wraps `pds4_tools`. Keyword-value style metadata is parsed with the `PVL` module, which is just wrapped.

Run `pds.test_io(n)` to run, where `n` is the number of test files that will be downloaded from the PDS and read in. The test data are in refdata.csv, and the list is just copied from `planetarypy`.

### Repo also contains:
+ parsing a PDS4 .dat format file into a tidy Python dictionary structure
+ reading in a PDS3 .IMG file from MSL Mastcam (with consequences for reading other IMG data and similar filetypes)

