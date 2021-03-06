import requests
from bs4 import BeautifulSoup
from urllib.request import urlretrieve
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

from deep_aqi import ROOT
from deep_aqi.src.helper_functions import no_overlaping_files

DOWNLOAD_PATH = os.path.join(ROOT, 'data', 'compressed')
START_YEAR = 2010
END_YEAR = 2017


"""MEASUREMENTS = 'ALL'
MEASUREMENTS = 'CRITERIA_GASES' - Ozone, SO2, CO, NO2
MEASUREMENTS = 'PARTICULATES' - PM2.5 & PM10
MEASUREMENTS = 'WEATHER' - Winds, Temperature, Pressure, RelHum and Dewpoint
MEASUREMENTS = 'TPL' - HAPs, VOCs, NONOxNOy, Lead
MEASUREMENTS = ['Ozone', 'WIND] - any number of measurements
MEASUREMENTS = ['CRITERIA_GASES', 'TPL'] - any number of groups
"""


ALLOW_MEASUREMENTS = ['CRITERIA_GASES', 'PARTICULATES', 'WEATHER']


def get_hourly_filenames():
    url = r'https://aqs.epa.gov/aqsweb/airdata/download_files.html'

    html_doc = requests.get(url)
    soup = BeautifulSoup(html_doc.content, 'html.parser')

    hfiles =  [link.get('href') for link
               in soup.findAll('a')
               if 'hourly' in link.get('href')]

    return hfiles


def date_fltr(year, start=START_YEAR, stop=END_YEAR):
    if (year >= start) and (year <= stop):
        return year
    else:
        return False


def measurement_fltr(condition):
    all_measurements = ['Ozone', 'SO2', 'CO', 'NO2', 'PM2.5/FEM Mass',
                        'PM2.5 non FRM/FEM Mass', 'PM10 Mass', 'PM2.5 Speciation',
                        'WIND', 'TEMP', 'PRESS', 'RelHumPress', 'HAPS', 'VOCS',
                        'NONOxNoy', 'LEAD']

    tag_dict = {
                'ALL': all_measurements,
                'CRITERIA_GASES': all_measurements[:4],
                'PARTICULATES': all_measurements[4:8],
                'WEATHER': all_measurements[8:12],
                'TPL': all_measurements[12:16]
                }

    measurements_ = []
    for el in condition:
        if el in tag_dict:
            measurements_.extend(tag_dict[el])
        else:
            measurements_.append(el)


    return measurements_


class file_info():
    def __init__(self, filename):
        self.filename = filename.split('.')[0]

    @property
    def year(self):
        try:
            return int(self.filename.split('_')[-1])
        except Exception:
            return 'BadYear'

    @property
    def measurement(self):
        measurement_dict = {
                             # criteria gases
                             '44201': 'Ozone',
                             '42401': 'SO2',
                             '42101': 'CO',
                             '42602': 'NO2',
                             # particulates
                             '88101': 'PM2.5/FEM Mass',
                             '88502': 'PM2.5 non FRM/FEM Mass',
                             '81102': 'PM10 Mass',
                             'SPEC': 'PM2.5 Speciation',
                             'RH': 'RelHumPress' # RH_DP
                            }
        measurement = self.filename.split('_')[1]

        if measurement in measurement_dict:
            measurement = measurement_dict[measurement]

        return measurement

    @property
    def download_link(self):
        base_url = r'https://aqs.epa.gov/aqsweb/airdata/'
        link = f'{base_url}{self.filename}.zip'
        return link

    def __str__(self):
        return f'{self.year} {self.measurement} {self.filename} '

def get_download_links():
    download_links = []
    fnames = get_hourly_filenames()
    for fname in fnames:
        f = file_info(fname)
        if date_fltr(f.year) and (f.measurement in measurement_fltr(ALLOW_MEASUREMENTS)):

            download_links.append(f.download_link)

    return download_links

def download_file(link):
    if not os.path.exists(DOWNLOAD_PATH):
        os.makedirs(DOWNLOAD_PATH)
    filename = link.split('/')[-1]
    print(f'Beginning download of {filename}')
    file_path = os.path.join(DOWNLOAD_PATH, filename)
    urlretrieve(link, file_path)
    print(f'File saved under: {file_path}')

def main():
    links = get_download_links()
    links = no_overlaping_files(links, DOWNLOAD_PATH)
    if links:
        with ThreadPoolExecutor(max_workers=25) as executor:
            future_to_url = {executor.submit(download_file, link): link for link in links}
            for future in as_completed((future_to_url)):
                future.result()


if __name__ == '__main__':
    main()
