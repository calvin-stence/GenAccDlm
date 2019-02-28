import glob2
import os
import re
import shutil

for file in glob2.glob('RAW_DATA_DUMP/*FT*'):
    new_name = re.sub('FT2','FT1',file)
    shutil.move(file,new_name)