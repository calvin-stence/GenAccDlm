import csv
import glob2
import time
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
import os
import re
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patheffects as path_effects


def main():
    lens_tests = create_thrupower_tests()
    job_search = re.compile(r'(VER[\w]?[\d]?)')
    lens_list = ['VERD1', 'VERD2', 'VERD3', 'VERC', 'VER1', 'VER0']
    ddf_search_dictionary = {
        'DBP Best Fit Tx': '',
        'DBP Best Fit Ty': '',
        'DBP Best Fit Rz': '',
        'FULL_LENS GMC': '',
        'Center GMC': '',
        'Center Power PV': '',
        'Center Power Average': ''
    }
    file_count = 1
    ddf_data_tracker = []
    test_result_figure_dictionary = {}
    rtc_fail_dictionary = {}
    dbp_fail_dictionary = {}
    print('--------------------')
    for fast_tool_file_path in glob2.glob('GENERATOR_ACCEPTANCE\**\FT*'):  # for each fast tool directory found
        print('Started job in ' + os.path.abspath(fast_tool_file_path))
        pdf_lab, pdf_generator, pdf_fast_tool = genacc_filename_get(os.path.abspath(fast_tool_file_path))
        with PdfPages('InternalGenAcc_' + pdf_lab + '_' + pdf_generator + '_' + pdf_fast_tool + '.pdf') as pdf:
            start = time.time()
            for item in lens_list:  # for each lens in that fast tool directory
                lens_figure = plt.figure(file_count, figsize=(21, 11))  # create a figure for that fast tool's data
                image_count = 1  # set the image count (for placing the image in the right position in the figure) to 1
                for measure_type_file_path in glob2.glob(
                        fast_tool_file_path + '\*'):  # for each type of measure (RTC and DBP)
                    for pmf_file in glob2.glob(
                            measure_type_file_path + '\\' + item + '*.PMF'):  # for each .PMF file in the current fast tool, lens, and RTC or DBP folder
                        job_identifier = item  # re.search(job_search, pmf_file) # figure out which
                        abs_filepath = os.path.abspath(pmf_file)
                        ddf_file = re.sub('.PMF', '', abs_filepath + '.DDF')
                        ddf_data = DdfDataGet(ddf_file, ddf_search_dictionary).ddf_contents
                        property_names, property_values, error_values, passing_status, failing_values = ddf_results_prep(
                            ddf_data)
                        # print('Lens DDF Data Ready')
                        # print(failing_values)
                        if 'RTC' in measure_type_file_path:
                            rtc_fail_dictionary[item] = failing_values
                        if 'DBP' in measure_type_file_path:
                            dbp_fail_dictionary[item] = failing_values
                        ddf_data_tracker.append(passing_status)
                        ddf_table(property_names, property_values, error_values, passing_status, image_count, item)
                        image_count = image_count + 1
                        lab, generator, fast_tool, measure = genacc_figurename_get(abs_filepath)
                        for tests, testparams in lens_tests.items():
                            testparams.update({'JOB': item + ' ' + measure})
                        for tests, testparams in lens_tests.items():
                            testparams.update({'POWERMAP': PmfDataGet(pmf_file, testparams).powermap})
                            visualize_powermap(testparams, image_count)
                            image_count = image_count + 1
                        # print('Lens PMF Plots Complete')
                lens_figure.suptitle(
                    'GenAcc Lab ' + lab + ', Generator ' + generator + ', ' + fast_tool + ', Lens ' + item,
                    size=25)  # add a title to that figure
                file_count = file_count + 1
                # lens_figure.subplots_adjust(left = .16, right=.95, top=.95, bottom=0.08)
                test_result_figure_dictionary[item] = lens_figure
                plt.close()
            lens_verdict_dictionary, test_result = determine_genacc_test_pass(rtc_fail_dictionary, dbp_fail_dictionary,
                                                                              lens_list)
            print('Lens Tests And Figures Complete')
            title_fig = plt.figure(figsize=(21, 11))
            text = title_fig.text(.5, .5,
                                  'Generator Acceptance Internal Report\n' + 'GenAcc Lab ' + lab + ', Generator ' + generator + ', ' + fast_tool,
                                  ha='center', va='center', size=20)
            text.set_path_effects([path_effects.Normal()])
            print('Begin Figure Saving')
            pdf.savefig(title_fig)
            plt.close()
            print('Lens Results: ' + str(lens_verdict_dictionary))
            result_table_figure = acceptance_result_figure(lens_verdict_dictionary, test_result, lens_list)
            pdf.savefig(result_table_figure)
            plt.close()
            print('Overall Test Result: ' + test_result)
            for item in lens_list:
                pdf.savefig(test_result_figure_dictionary[item])
            print(
                'PDF Saved: ' + 'Generator Acceptance Internal Report' + ' GenAcc Lab ' + lab + ', Generator ' + generator + ', ' + fast_tool)
            end = time.time()
            print('Script Completed in ' + str(end - start) + ' Seconds')
            print('--------------------')

        # plt.show()
        # plt.savefig(job + '_' + measure_type + '_' + power_quantity + '_' + measured_power_type + '.png',
        #            bbox_inches='tight')


def determine_genacc_test_pass(rtc_failing_results, dbp_failing_results, lens_list):
    # print(rtc_failing_results)
    # print(dbp_failing_results)
    lens_verdict_dictionary = {}
    for item in lens_list:
        lens_verdict_dictionary[item] = ''
    fail_count = 0
    for lens, failing_params in rtc_failing_results.items():
        # print(failing_params)
        if 'FULL_LENS GMC' in failing_params:
            if 'FULL_LENS GMC' in dbp_failing_results[lens]:
                lens_verdict_dictionary[lens] = 'FAIL'
                pass
        if re.search('Center Power Average',str(failing_params)) or re.search('Center GMC',str(failing_params)) in failing_params:
            if re.search('Center Power Average', str(failing_params)) or re.search('Center GMC', str(failing_params)) in dbp_failing_results[lens]:
                lens_verdict_dictionary[lens] = ' CENTER DEFECT '
        if 'FULL_LENS Power Average' in failing_params:
            if 'FULL_LENS Power Average' in dbp_failing_results[lens]:
                lens_verdict_dictionary[lens] = lens_verdict_dictionary[lens] + ' CENTER THICK '
        if re.search('DBP Best Fit',str(failing_params)):
            lens_verdict_dictionary[lens] = lens_verdict_dictionary[lens] + ' POSITIONING '
    for lens, failing_params in lens_verdict_dictionary.items():
        if 'FAIL' in lens_verdict_dictionary[lens]:
            fail_count = fail_count + 1
    if fail_count > 1:
        test_result = 'FAIL'
    else:
        test_result = 'ACCEPTED'
    return lens_verdict_dictionary, test_result


def genacc_filename_get(abs_filepath):
    abs_filepath_regex = re.compile('\\\([\w]+)\\\([\d]+[\w]?)\\\(\w\w\d)')
    search_result = re.search(abs_filepath_regex, abs_filepath)
    lab = search_result.group(1)
    generator_number = search_result.group(2)
    fast_tool = search_result.group(3)
    return lab, generator_number, fast_tool


def genacc_figurename_get(abs_filepath):
    abs_filepath_regex = re.compile('\\\([\w]+)\\\([\d]+[\w]?)\\\(\w\w\d)\\\(\w\w\w)_DATA')
    search_result = re.search(abs_filepath_regex, abs_filepath)
    lab = search_result.group(1)
    generator_number = search_result.group(2)
    fast_tool = search_result.group(3)
    measure_type = search_result.group(4)
    return lab, generator_number, fast_tool, measure_type


def create_thrupower_tests():
    test_dpt = {
        'JOB': '',
        'MEASURE_TYPE': 'E',
        'POWER_QUANTITY': 'D',
        'MEASURED_POWER_TYPE': 'T'
    }
    test_cyl = {
        'JOB': '',
        'MEASURE_TYPE': 'E',
        'POWER_QUANTITY': 'C',
        'MEASURED_POWER_TYPE': 'T'
    }
    thrupower_tests = {
        'dpt': test_dpt,
        'cyl': test_cyl
    }
    return thrupower_tests


def test_ddf():
    infile = 'GENERATOR_ACCEPTANCE\TEST_LAB_1\\26001\FT1\DBP_DATA\VERD3_2018-10-18_17.15.38.DDF'
    image_count = 1
    item = 'VERD3'
    ddf_search_dictionary = {
        'DBP Best Fit Tx': '',
        'DBP Best Fit Ty': '',
        'DBP Best Fit Rz': '',
        'FULL_LENS GMC': '',
        'Center GMC': '',
        'Center Power PV': '',
        'Center Power Average': ''
    }
    ddf_data = DdfDataGet(infile, ddf_search_dictionary).ddf_contents
    property_names, property_values, error_values, passing_status = ddf_results_prep(ddf_data)
    ddf_table(property_names, property_values, error_values, passing_status, image_count, item)


def ddf_results_prep(results_dictionary):
    error_values = []
    passing_status = []
    property_names = list(results_dictionary.keys())
    property_values = list(results_dictionary.values())
    float_property_values = []
    failing_values = []
    for row in property_values:
        float_property_values.append([float(i) for i in row])
    for index, row in enumerate(float_property_values):
        error = abs(row[1]) - row[2]
        error_values.append(error)
        if int(row[0]) == 1:
            passing_status.append("PASS")
        else:
            passing_status.append("FAIL")
            failing_values.append(property_names[index])
    return property_names, float_property_values, error_values, passing_status, failing_values


def get_bar_multiplier(max_val, min_val, val):
    return (val - min_val) / (max_val - min_val)


def acceptance_result_figure(test_result_dictionary, test_result, lens_list):
    test_result_fig = plt.figure(99, figsize=(21, 11))
    ax = plt.subplot(335)
    ax.axis('tight')
    ax.axis('off')
    # print(property_names)
    # print(property_values)
    colors = []
    acceptance_list = []
    row_labels = []
    row_labels.append('Overall Test Result')
    row_labels = row_labels + lens_list
    acceptance_list.append([test_result])
    if test_result == 'ACCEPTED':
        colors.append((0, 1, 0))
    if test_result != 'ACCEPTED':
        colors.append((1, 0, 0))
    # todo figure out why some are coming out as orange when they shouldn't be failing the logic test here
    for lens, acceptance in test_result_dictionary.items():
        # print(colors)
        acceptance_string = str(acceptance)
        if lens == 'Overall Test Result':
            print('Potato')
            pass
        if str(acceptance) == '':
            acceptance_list.append(['PASS'])
            colors.append((0, 1, 0))
            pass
        if str(acceptance) == 'FAIL':
            acceptance_list.append(['FAIL'])
            colors.append((1, 0, 0))
            pass
        if str(acceptance) != '':
            acceptance_list.append(['DEFECTS: ' + acceptance])
            colors.append((1, .5, 0))  # (255,0,0))

    # print(colors)
    table_cells = acceptance_list
    # print(table_cells)
    plt.table(cellText=table_cells, rowLabels=row_labels, colLabels=['Result'],
              rowColours=colors, loc='center')
    ax.set_title('Overall and Invidual Lens Results')


def ddf_table(property_names, property_values, error_values, passing_status, figure_index, lens_name):
    ax = plt.subplot(230 + figure_index)
    # print(property_names)
    # print(property_values)
    colors = []
    for x in passing_status:
        if x == 'PASS':
            colors.append((0, 1, 0))  # (255,0,0))
        else:
            colors.append((1, 0, 0))  # (0,255,0))

    # print(colors)
    table_cells = row_to_column(passing_status)
    property_names_list = property_names
    table_cells = add_column(table_cells, property_values)
    table_cells = add_column(table_cells, error_values)
    # print(table_cells)
    ax.axis('tight')
    ax.axis('off')
    plt.table(cellText=table_cells, rowLabels=property_names, colLabels=['Passing Status', 'Measure Value', 'Error'],
              rowColours=colors, loc='center')
    ax.set_title(lens_name + ', Go-No-Go')
    # plt.imshow(ax)
    # plt.yticks(range(property_names),property_names)
    # plt.show()


def add_column(list1, list2):
    for index, row in enumerate(list1):
        row.append(list2[index])
        # print(row)
    return list1


def row_to_column(list):
    transposed_list = []
    for i in range(len(list)):
        transposed_list.append([list[i]])
    return transposed_list


def ddf_plot(property_names, property_values, passing_status, figure_index, lens_name):
    ax = plt.subplot(230 + figure_index)
    # print(property_names)
    # print(property_values)
    plt.barh(property_names, property_values)
    ax.set_title(lens_name + ', GNG')
    # plt.imshow(ax)
    # plt.yticks(range(property_names),property_names)
    plt.show()


class DdfDataGet():
    # todo get DBP Tx, Ty, Rz, Full Lens GMC, Center GMC, Center Power PV, Center Power Average
    def __init__(self, file, search_dictionary):
        self.file = file
        with open(self.file) as csvfile:
            file_reader = csv.reader(csvfile, delimiter=';', lineterminator='\n')
            filedata = DdfDataGet.preprocess_ddf(self, list(file_reader))
            output_dictionary = {}
            for search, val in search_dictionary.items():
                for row in filedata:
                    if search in output_dictionary.keys():
                        pass
                    for i in range(len(row)):
                        if re.search(search, row[i]):
                            output_dictionary.update({search: row[3:6]})
            self.ddf_contents = output_dictionary

    def preprocess_ddf(self, list):  # take in the entire pmf file in the form of a list
        for row in list:  # for all rows in the input list form pmf
            for i in range(len(row)):  # iterate across each row of the pmf
                row[i] = re.sub('DD=', '', row[i])  # remove all instances of pp at the beginning of powermap rows
                row[i] = re.sub('\?', '0', row[
                    i])  # set unmeasured parts of the powermap (represented by '?' in the raw data to 99999 so they can be masked later
        return list  # return the list-form ready pmf for powermap extraction


class PmfDataGet():
    def __init__(self, file, powermap_params):
        self.file = file
        self.powermap_params = powermap_params
        pmfmt_search = re.compile(r'PMFMT=')

        with open(self.file) as csvfile:
            file_reader = csv.reader(csvfile, delimiter=';', lineterminator='\n')
            filedata = PmfmtParse.preprocess_pmf(self, list(file_reader))
            powermaps = []
            for index, row in enumerate(filedata):
                if re.search(pmfmt_search, row[0]):
                    power_matrix_properties = PmfmtParse(row)
                    measure_type_bool = power_matrix_properties.measure_type == self.powermap_params.get('MEASURE_TYPE')
                    power_quantity_bool = power_matrix_properties.power_quantity == self.powermap_params.get(
                        'POWER_QUANTITY')
                    measured_power_type_bool = power_matrix_properties.measured_power_type == self.powermap_params.get(
                        'MEASURED_POWER_TYPE')
                    if measure_type_bool and power_quantity_bool and measured_power_type_bool:
                        powermap_raw = np.array(filedata[index + 1:index + 1 + power_matrix_properties.x_col_count])
                        powermap = powermap_raw.astype(float)
                        self.powermap = powermap


def visualize_powermap(powermap_params, figure_index):
    job = powermap_params.get('JOB')
    powermap = powermap_params.get('POWERMAP')  #
    measure_type = powermap_params.get('MEASURE_TYPE')  # error value, measure value, or refernce value
    power_quantity = powermap_params.get('POWER_QUANTITY')  # cylinder or spherical equivalent diopter
    measured_power_type = powermap_params.get('MEASURED_POWER_TYPE')  # reflection or transmission
    subplot_name = job + ', ' + measure_type + ', ' + power_quantity + ', ' + measured_power_type
    # fig = plt.figure()
    ax1 = plt.subplot(230 + figure_index)
    ax1.set_ylabel('Y position, mm')
    ax1.set_xlabel('X position, mm')
    ax1.set_title(subplot_name)
    copy_colormap = plt.cm.nipy_spectral
    palette = copy_colormap
    palette.set_bad('w', 1.0)
    masked_powermap = np.ma.masked_where(powermap > 20, powermap)
    if power_quantity == 'C':
        v_max = 0.3
        v_min = -.3
    if power_quantity == 'D':
        v_max = 0.25
        v_min = -0.25
    plt.imshow(masked_powermap, cmap=palette, interpolation='gaussian', vmin=v_min, vmax=v_max)

    plt.colorbar(label='Power, dpt')
    # plt.savefig(job + '_' + measure_type + '_' + power_quantity + '_' + measured_power_type + '.png',
    #            bbox_inches='tight')


class PmfmtParse():
    def __init__(self, pmfmt_list):
        self.pmfmt_list = pmfmt_list
        self.eye = pmfmt_list[1]  # which eye, left, right or both (L, R, B)
        self.measured_power_type = pmfmt_list[2]  # B, F, or T, back, front, or transmitted power
        self.power_quantity = pmfmt_list[3]  # D, C, or A - spherical equivalent power, cylinder power, or cylinder axis
        self.measure_type = pmfmt_list[4]  # M, T, or E- measured, theoretical, or error
        self.x_col_count = int(pmfmt_list[5])  # number of X columns (integer)
        self.y_col_count = int(pmfmt_list[6])  # number of Y columns (integer)
        self.x_size = pmfmt_list[7]  # x size (in millimeters, the actual physical size of the dataset)
        self.y_size = pmfmt_list[8]  # y size (in millimeters, the actual physical size of the dataset)
        self.index = pmfmt_list[9]  # the index of the material, for generator acceptance lenses

    def preprocess_pmf(self, list):  # take in the entire pmf file in the form of a list
        for row in list:  # for all rows in the input list form pmf
            for i in range(len(row)):  # iterate across each row of the pmf
                row[i] = re.sub('PP=', '', row[i])  # remove all instances of pp at the beginning of powermap rows
                row[i] = re.sub('\?', '99999', row[
                    i])  # set unmeasured parts of the powermap (represented by '?' in the raw data to 99999 so they can be masked later
        return list  # return the list-form ready pmf for powermap extraction


if __name__ == "__main__":
    main()
