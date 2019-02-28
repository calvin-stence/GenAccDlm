import csv
import glob2
import time
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
import os
import re
import shutil
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patheffects as path_effects

for file in glob2.glob('test_input/manual_art/art_m_ddf/*.csv'):
    with open(file) as csvfile:
        jobs_tested = csv.reader(csvfile, delimiter=';', lineterminator='\r\n')
        listjobs = list(jobs_tested)
        print('potato')