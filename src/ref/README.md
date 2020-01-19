This directory holds PDS3 format files (or "label fragments"). These are generally referenced in the labels with a ^STRUCTURE pointer of table (.DAT) files, and contain the column definitions.

A better way to handle these is to maintain some kind of structured data reference (e.g. a database table) that correctly maps various instruments / missions / data versions to the reference files. For now---for dev and testing purposes---the directory structure is just [INSTRUMENT_HOST_NAME]/[INSTRUMENT_ID]/\*fmt, and I'll find them with a `glob` search.
