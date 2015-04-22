#!/usr/bin/python

import argparse
import ast

def pds_util():
    return

def setup_parser():
    parser = argparse.ArgumentParser(description='Search the PDS.')
    parser.add_argument('--api', dest='api', choices='eng', default='eng',
        description='Specify which search method / API to use.')
    parser.add_argument('--archive_status',type=ast.literal_eval,action='store',
        dest='archive_status',description='Used to identify products with a '+
        'specific archive status (e.g., Archived)')
    parser.add_argument('--identifier',type=ast.literal_eval,action='store',
        dest='identifier',description='Identifies a product or multiple '+
        'verions of a product. Maps to the logical_identifier attribute '+
        'specified in a product label or the combination of the '+
        'logical_identifier and version_id attributes. The former case may '+
        'return multiple versions of a product whereas the latter case '+
        'should return one product. This parameter also maps to the '+
        'alternate_id attribute located in the Alias class which may be '+
        'specified in a product label. This is a user-specified attribute '+
        'that will likely contain the value for the DATA_SET_ID or '+
        'PRODUCT_ID keywords for products migrated from PDS3 to PDS4.')
    return

def check_args():

if __name__ == '__main__':
    args = setup_parser().parse_args()
    args = check_args(args)
    pds_util()
