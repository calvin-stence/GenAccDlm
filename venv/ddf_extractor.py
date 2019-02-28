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

def test():
    ddf_obj = DdfDataGet('test_input/ddf_extractor/IFB_28067_FT1_VER1_RTC.DDF')
    plt.figure(1)
    ddf_obj.visualize_ddf()
    plt.show()


class DdfDataGet:
    def __init__(self, file, list_input=None):
        self.file = file
        self.ddf_search_dictionary = {
            'DBP Best Fit Tx': '',
            'DBP Best Fit x': '',
            'DBP Best Fit Ty': '',
            'DBP Best Fit y': '',
            'DBP Best Fit Rz': '',
            'Block Center':'',
            'FULL_LENS GMC': '',
            'GMC':'',
            'Center GMC': '',
            'Center Power PV': '',
            'Center Power Average': '',
            'FULL_LENS Power Average': '',
            'SPH':'',
            'CYL':'',
            'In Corridor':'',
            'Out Corridor':''
        }
        self.lens_id_search = re.search(r'(\d+)_(\w\d+)_(\w+-?\d+)_(\d+)', os.path.basename(file))
        self.surfacing_status_search = re.search(r'(_\w*surfaced)', os.path.basename(file))
        if self.surfacing_status_search:
            self.surfaced_or_unsurfaced = self.surfacing_status_search.group(1)
        else:
            self.surfaced_or_unsurfaced = ''
        if self.lens_id_search:
            # try:
            self.job = self.lens_id_search.group(1)
            self.base = self.lens_id_search.group(2)
            self.rx = self.lens_id_search.group(3)
            self.lens_number = self.lens_id_search.group(4)
            self.lens_description = 'Job ' + self.job + '\n' + self.base + ', ' + self.rx + ', Lens#' + self.lens_number
        try:
            if list_input is None:
                with open(self.file) as csvfile:
                    file_reader = csv.reader(csvfile, delimiter=';', lineterminator='\n')
                    filedata = DdfDataGet.preprocess_ddf(self, list(file_reader))
                    output_dictionary = {}
                    for search, val in self.ddf_search_dictionary.items():
                        for row in filedata:
                            if search in output_dictionary.keys():
                                continue
                            for i in range(len(row)):
                                if re.search(search, row[i]):
                                    output_dictionary.update({search: row[3:6]})
                    self.ddf_contents = output_dictionary
                    readable_ddf_contents = {}
                    for key, value in self.ddf_contents.items():
                        new_value_list = []
                        passing_status = int(value[0])
                        if passing_status == 0:
                            new_value_list.append('FAIL')
                        if passing_status == 1:
                            new_value_list.append('PASS')
                        new_value_list.append(value[1])
                        if abs(float(value[1])) > abs(float(value[2])):
                            amount_over_spec_limit = str(abs(float(value[1])) - abs(float(value[2])))
                            truncated_amount_over_spec_limit = amount_over_spec_limit[0:5]
                            new_value_list.append(truncated_amount_over_spec_limit)
                        else:
                            new_value_list.append('N/A')
                        readable_ddf_contents.update({key: new_value_list})
                    self.readable_ddf_contents = readable_ddf_contents
            if list_input is not None:
                self.list_ddf_extraction(list_input)
        except FileNotFoundError:
            print('\nNo .DDF found for ' + os.path.basename(file) + '--check if it is missing')
            self.ddf_contents = self.ddf_search_dictionary

    def preprocess_ddf(self, list):  # take in the entire ddf file in the form of a list
        for row in list:  # for all rows in the input list form pmf
            for i in range(len(row)):  # iterate across each row of the pmf
                row[i] = re.sub('DD=', '', row[i])  # remove all instances of DD at the beginning of rows
                row[i] = re.sub('T', '', row[i])
                row[i] = re.sub('\?', '0', row[i])  # set unmeasured parts of the powermap (represented by '?' in the raw data to 99999 so they can be masked later
        return list  # return the list-form ready pmf for powermap extraction

    def list_ddf_extraction(self, list_input):
        output_dictionary = {}
        filedata = DdfDataGet.preprocess_ddf(self, list_input)
        for search, val in self.ddf_search_dictionary.items():
            for row in filedata:
                if search in output_dictionary.keys():
                    continue
                for i in range(len(row)):
                    if re.search(search, row[i]):
                        output_dictionary.update({search: row[3:6]})
        self.ddf_contents = output_dictionary
        readable_ddf_contents = {}
        for key, value in self.ddf_contents.items():
            new_value_list = []
            passing_status = int(value[0])
            if passing_status == 0:
                new_value_list.append('FAIL')
            if passing_status == 1:
                new_value_list.append('PASS')
            new_value_list.append(value[1])
            if abs(float(value[1])) > abs(float(value[2])):
                amount_over_spec_limit = str(abs(float(value[1])) - abs(float(value[2])))
                truncated_amount_over_spec_limit = amount_over_spec_limit[0:5]
                new_value_list.append(truncated_amount_over_spec_limit)
            else:
                new_value_list.append('N/A')
            readable_ddf_contents.update({key: new_value_list})
        self.readable_ddf_contents = readable_ddf_contents


    def visualize_ddf(self):
        try:
            colors = []
            table_cells = list(self.readable_ddf_contents.values())
            property_names = list(self.readable_ddf_contents.keys())
            # ax.axis('tight')
            colors = []
            for index, item in enumerate(table_cells):
                if item[0] == 'PASS':
                    colors.append((0, 1, 0))  # (255,0,0))
                else:
                    colors.append((1, 0, 0))  # (0,255,0))
                if len(item)<3:
                    table_cells[index] = ['NONE', 'NONE','NONE']
                    colors[index] = (1,0,0)

            data_table = plt.table(cellText=table_cells, rowLabels=property_names, rowColours=colors,
                                   colLabels=['Passing\nStatus', 'Measured\nValue', 'Exceeds Spec\nLimit By'], loc='center')
            data_table.set_fontsize(20)
            data_table.scale(.5, 2.5)
            plt.title('Go-No-Go Results')
            plt.axis('off')
        except IndexError:
            print('Something went wrong with the DDF table, replacing it with placeholder, perhaps the DDF is missing?')
            #ax = plt.subplot(230 + figure_index)
            #ax.set_title('Error -- check if DDF exists')

if __name__ == "__main__":
    test()