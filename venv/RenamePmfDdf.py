import re
import os
import shutil
import glob2


def main():
    print('potato')
    for file in glob2.glob('dataconversion\\*27008*'):
        print(file)
        new_file = re.sub(r'27008', '26019', file)
        new_file_ft = re.sub(r'FT1', 'FT2', new_file)
        shutil.copy(file, new_file_ft)


def genacc_rawdata_filename_get(abs_filepath):
    abs_filepath_regex = re.compile(r'([\w]+[\d]?)_([\d]+[\w]?)_(\w\w\d)_(\w\w\w\w[\W]?[\d]?)_(\w\w\w)')
    search_result = re.search(abs_filepath_regex, abs_filepath)
    lab = search_result.group(1)
    generator_number = search_result.group(2)
    fast_tool = search_result.group(3)
    lens = search_result.group(4)
    measure_type = search_result.group(5)
    return lab, generator_number, fast_tool, lens, measure_type

if __name__ == "__main__":
    main()