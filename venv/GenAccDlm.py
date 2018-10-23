import csv
#import glob2
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import pprint as pp
import numpy as np
import shutil
import os
import re

def main():
    test_dpt = {
        'MEASURE_TYPE': 'E',
        'POWER_QUANTITY': 'D',
        'MEASURED_POWER_TYPE': 'T'
    }
    file = 'dlm_data\VERD3_2018-10-18_17.15.38.PMF'
    test = DLMDataGet(file,test_dpt)

class DLMDataGet():
    def __init__(self, file, powermap_params):
        self.file = file
        self.powermap_params = powermap_params
        pmfmt_search = re.compile(r'PMFMT=')
        with open(self.file) as csvfile:
            file_reader = csv.reader(csvfile, delimiter=';',lineterminator='\n')
            filedata = PmfmtParse.preprocess_pmf_file(self,list(file_reader))
            powermaps = []
            for index, row in enumerate(filedata):
                if re.search(pmfmt_search,row[0]):
                    power_matrix_properties = PmfmtParse(row)
                    measure_type_bool = power_matrix_properties.measure_type == self.powermap_params.get('MEASURE_TYPE')
                    power_quantity_bool = power_matrix_properties.power_quantity == self.powermap_params.get('POWER_QUANTITY')
                    measured_power_type_bool = power_matrix_properties.measured_power_type == self.powermap_params.get('MEASURED_POWER_TYPE')
                    if measure_type_bool and power_quantity_bool and measured_power_type_bool:
                        powermap_raw = np.array(filedata[index+1:index+1+power_matrix_properties.x_col_count])
                        powermap = powermap_raw.astype(float)
                        visualize_powermap(powermap)
                    #print(powermap)
                    #print(power_matrix_properties.eye)
            #print(filedata)
            #print(self.test_dictionary)

def visualize_powermap(powermap):
    copy_colormap = plt.cm.plasma
    palette = copy_colormap
    palette.set_bad('w',1.0)
    masked_powermap = np.ma.masked_where(powermap>5, powermap)
    plt.imshow(masked_powermap, cmap=palette, interpolation='bilinear')
    plt.colorbar()
    #curves = 10
    #m = max([max(row) for row in powermap])
    #levels = np.arange(0, m, (1 / float(curves)) * m)
    #plt.contour(powermap, colors="white", levels=levels)
    plt.show()

def gen_acc_test():
    return 0


class PmfmtParse():
    def __init__(self, pmfmt_list):
        self.pmfmt_list = pmfmt_list
        self.eye = pmfmt_list[1] #which eye, left, right or both (L, R, B)
        self.measured_power_type = pmfmt_list[2]  # B, F, or T, back, front, or transmitted power
        self.power_quantity = pmfmt_list[3]  # D, C, or A - spherical equivalent power, cylinder power, or cylinder axis
        self.measure_type = pmfmt_list[4] # M, T, or E- measured, theoretical, or error
        self.x_col_count = int(pmfmt_list[5])  # number of X columns (integer)
        self.y_col_count = int(pmfmt_list[6])  # number of Y columns (integer)
        self.x_size = pmfmt_list[7]  # x size (in millimeters, the actual physical size of the dataset)
        self.y_size = pmfmt_list[8]  # y size (in millimeters, the actual physical size of the dataset)
        self.index = pmfmt_list[9]  # the index of the material, for generator acceptance lenses
    def preprocess_pmf_file(self,list):
        for row in list:
            for i in range(len(row)):
                row[i] = re.sub('PP=','',row[i])
                row[i] = re.sub('\?','99999',row[i])
        return list




if __name__ == "__main__":
    main()

