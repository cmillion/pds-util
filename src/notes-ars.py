#!/usr/local/bin/python2.7
import pds
reload(pds)
import matplotlib.pyplot as plt
import pds_bit_mask as pbm
import pds_format_mask as pfm

"""
# MSL Mastcam Test Case
img = 'test/data/MSL/Mastcam/0174MR0009350080201949C00_DRCX.IMG'
lbl = 'test/data/MSL/Mastcam/0174MR0009350080201949C00_DRCX.lbl'

label = pds.read_label(lbl)
image = pds.read_image(img,lbl)
"""
# MER Pancam Test Case                                           fnum sol_day     bit masking
images = ['test/data/MER/Pancam/1p143982066eff3336p2621l3m1.img', # 0 sol0178 edr 2#0000111111111111#
          'test/data/MER/Pancam/1p143982066mrd3336p2621l3m1.img', # 1 sol0178 rdr 2#0111111111111111#
          'test/data/MER/Pancam/1p143982114mrl3336p2621l7m1.img', # 2 sol0178 rdr 2#0111111111111111#
          'test/data/MER/Pancam/1p187211918rsd64kcp2598l7m1.img', # 3 sol0665 rdr   0000111111111111
          'test/data/MER/Pancam/1p187211967eff64kcp2598r1m1.img', # 4 sol0665 edr 2#0000000011111111#
          'test/data/MER/Pancam/1p322777859effadvrp2401l2m1.img', # 5 sol2192 edr 2#0000000011111111#
          'test/data/MER/Pancam/1p322778119effadvrp2401l5m1.img', # 6 sol2192 edr 2#0000000011111111#
          'test/data/MER/Pancam/1p386874914mrdbr43p2551l7m1.img', # 7 sol2914 rdr 2#0111111111111111#
          'test/data/MER/Pancam/1p386874914mrnbr43p2551l7m1.img', # 8 sol2914 rdr 2#0111111111111111#
          '1p138122848rsd2600p2621l7m1.img',                      # 9 sol0112 rdr   0000111111111111
          '1p137056262rsd2002p2104l7m1.img']                      #10 sol0100 rdr   0000111111111111
fnum = 0

'''The method below provides the same output as with the data being processed
   with this method. A new module may need to be scripted to test this...'''
masking = pbm.bit_mask(images[fnum]) #Extract bit mask from .img file
mask_list = pbm.mask_list(masking) #Converts mask to a list
array = pds.read_image(images[fnum]) #Assigns image data to location in memory
img = pbm.mask_apply(array,mask_list) #Applies bit mask and assembles new array
#img = pds.read_image(images[fnum])

'''Two images are plotted to show the similarities between the plotted input
   data (array) and the plotted output data (img).'''
plt.figure()
plt.imshow(img)
plt.show()

plt.figure()
plt.imshow(array)
plt.show()
"""
for i in images:
    lab = pds.read_label(i)
    print lab['IMAGE']
    img = pds.read_image(i)
    plt.figure()
    plt.imshow(img)
    plt.show()
"""
