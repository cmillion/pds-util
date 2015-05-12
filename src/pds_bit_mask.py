#!/usr/local/bin/python2.7

import re
import pds
import numpy as np

def bit_mask(imagename):
    '''Extract the bit mask from .img file'''
    f = open(imagename,'r')
    text = f.read()
    fname = 'text.txt'
    g = open(fname,'w')
    g.write(text)

    '''regex1 used for "rsd-type" bit masking'''
    regex1 = re.compile('(?<=.SAMPLE_BIT_MASK.................=.)(................)')

    '''regex2 used for all other bit masking'''
    regex2 = re.compile('(?<=.SAMPLE_BIT_MASK.................=...)(................)')

    h=open(fname,'r')
    masking1_rsd = re.findall(regex1,h.read())
    masking1 = str(masking1_rsd[0])

    if '#' in masking1:
        i = open(fname,'r')
        masking2_other = re.findall(regex2,i.read())
        masking2 = str(masking2_other[0])
        masking = masking2
        print('# in masking1: not rsd-type')
    else:
        masking = masking1
        print('# not in masking1: rsd-type')

    return masking

def mask_list(masking):
    '''Convert bit mask to a list of integers'''
    masking_list = list(masking)
    masking_list_int = []
    for i in range(0,len(masking_list)):
        masking_list_intt = int(masking_list[i])
        masking_list_int.append(masking_list_intt)

    #print masking_list_int

    return masking_list_int

def mask_apply(array,mask_list):
    '''Convert image data to lists of integers and apply the bit mask to them'''
    print('Applying Bitmask...')
    unmasked_array = []
    for i in range(0,len(array)):
        array_row = array[i]
        unmasked_row = []
        for j in range(0,len(array_row)):
            pixel = '{0:016b}'.format(array_row[j],base=2)
            pixel_list = list(pixel)
            pixel_list_int = [int(x) for x in pixel_list]
            mask_applied = [mask_list[x] | pixel_list_int[x] for x in range(0,len(mask_list))]
            mask_applied_str = [str(x) for x in mask_applied]
            mask_applied_join = ''.join(mask_applied_str)
            mask_applied_int64 = np.int64(mask_applied_join,2)
            #print mask_applied_int64,'',type(mask_applied_int64),'','COLUMN: ',j
            unmasked_row.append(mask_applied_int64)
        unmasked_array.append(unmasked_row)

    print('Printing image...')

    return unmasked_array
