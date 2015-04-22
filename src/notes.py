%pylab
import pds
reload(pds)

# MSL Mastcam Test Case
img = 'test/data/MSL/Mastcam/0174MR0009350080201949C00_DRCX.IMG'
lbl = 'test/data/MSL/Mastcam/0174MR0009350080201949C00_DRCX.lbl'

label = pds.read_label(lbl)
image = pds.read_image(img,lbl)

# MER Pancam Test Case
images = ['test/data/MER/Pancam/1p143982066eff3336p2621l3m1.img',
          'test/data/MER/Pancam/1p143982066mrd3336p2621l3m1.img',
          'test/data/MER/Pancam/1p143982114mrl3336p2621l7m1.img',
          'test/data/MER/Pancam/1p187211918rsd64kcp2598l7m1.img',
          'test/data/MER/Pancam/1p187211967eff64kcp2598r1m1.img',
          'test/data/MER/Pancam/1p322777859effadvrp2401l2m1.img',
          'test/data/MER/Pancam/1p322778119effadvrp2401l5m1.img',
          'test/data/MER/Pancam/1p386874914mrdbr43p2551l7m1.img',
          'test/data/MER/Pancam/1p386874914mrnbr43p2551l7m1.img']

for i in images:
    lab = pds.read_label(i)
    print lab['IMAGE']
    img = pds.read_image(i)
    plt.figure()
    plt.imshow(img)

print '       '+bin(108784010)
print bin(label1['IMAGE']['SAMPLE_BIT_MASK'])
print '            '+bin(label1['IMAGE']['SAMPLE_BIT_MASK'] | 108784010)
