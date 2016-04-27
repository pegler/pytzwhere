from __future__ import absolute_import, division, print_function, unicode_literals

import re


def write_csv_for_tzwhere_from_json(input_path='tz_world.json', output_path='tz_world.csv'):
    """
    writing a .csv for pytzwhere
    format: tz_name, x1 y1, x2 y1, ...,xn yn\n
    :param input_path:
    :return:
    """
    f = open(input_path, 'r')
    print('Parsing data from .json')
    n = 0
    output_file = open(output_path, 'w')
    for row in f:

        if n % 1000 == 0:
            print('line', n)

        n += 1
        # print(row)
        tz_name_match = re.search(r'\"TZID\":\s\"(?P<name>.*)\"\s\}', row)
        # tz_name = re.search(r'(TZID)', row)
        # print(tz_name)
        if tz_name_match is not None:

            tz_name = tz_name_match.group('name').replace('\\', '')
            output_file.write(tz_name + ',')

            coordinates = re.findall('[-]?\d+\.?\d+', row)
            # print(coordinates)

            nr_coordinates = len(coordinates) - 1
            i = 0
            for coord in coordinates:
                if i % 2 == 0:
                    output_file.write(coord + ' ')
                else:
                    output_file.write(coord)
                    if i < nr_coordinates:
                        output_file.write(',')
                i += 1

            if i % 2 != 0:
                raise ValueError(i, 'Floats in line', n, ' found. Should be even (pairs or (x,y) )')

            output_file.write('\n')

    print('Done\n')


if __name__ == '__main__':
    write_csv_for_tzwhere_from_json(input_path='tz_world.json', output_path='tz_world.csv')
