import sys,glob
from PIL import Image
from concurrent.futures import ProcessPoolExecutor
def f(p):
    im=Image.open(p)
    if im.mode!='RGBA': im.convert('RGBA').save(p,compress_level=1); return 1
    return 0
with ProcessPoolExecutor() as ex: print(sum(ex.map(f,sorted(glob.glob(sys.argv[1]+'/*.png')))))
