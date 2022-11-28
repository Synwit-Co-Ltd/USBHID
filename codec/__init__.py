import collections

from . import codec
from . import ramdisk


Codecs = collections.OrderedDict([
    ('None',     codec.Codec),
    ('RAMDisk',  ramdisk.RAMDisk),
])
