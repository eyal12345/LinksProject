import re
import requests # pip install requests
import datetime
import argparse
import yaml # pip install pyyaml
import json
import progressbar # pip install progressbar2
import io
import os

# usage: -r "https://edition.cnn.com" -d 1 -f "yml"
# save in repository: git add . && git commit -m "changes" && git push

# user input
parser = argparse.ArgumentParser(description='enter root link with max depth for scanning')
parser.add_argument('-r', '--root', help="main page from start scan", type=str, required=True)
parser.add_argument('-d', '--depth', help="max depth for scanning", type=int, required=True)
parser.add_argument('-f', '--format', help="file result format for display", type=str, required=True)
parser.add_argument('-s', '--search', help="get links by search words", type=str, required=False)

# get initial arguments
args = vars(parser.parse_args())
root ,max_depth ,format = args['root'] ,args['depth'] ,args['format']
values_search = args['search']
timestamp = datetime.datetime.now().strftime('%m-%d-%Y %H-%M-%S')

# global variables
serial = 0
visited = []
file_path = root.split('.')[1] + "_md" + str(max_depth) + "_" + timestamp + "." + format

# design for progress bar
widgets = [
    progressbar.Timer(format='elapsed time: %(elapsed)s'), ' ',
    progressbar.Bar('*'), '',
    progressbar.Percentage(), '',
]

# create custom file format by user choise
def create_file_format():
    global serial
    key = 'url_' + str(serial)
    serial = serial + 1
    with io.open(file_path, 'w', encoding='utf8') as file:
        if format == 'yaml' or format == 'yml':
            yaml.dump({key: {"path": root ,"depth": 0 ,"access": try_open_url(root)}}, file, default_flow_style=False, allow_unicode=True, sort_keys=False)
        elif format == 'json':
            json.dump({key: {"path": root ,"depth": 0 ,"access": try_open_url(root)}}, file, indent=4)
        else:
            raise Exception('the format is invalid')

# read from ignore file list of extension unnecessaries
def get_extension_unnecessaries():
    ignore = []
    if os.path.exists("ignore.txt"):
        with open("ignore.txt" ,"r") as file:
            content = file.read()
            ignore = content.split('\n')
    return ignore

# extract urls set from general url
def extract_urls(link):
    try:
        response = requests.get(link ,headers={'User-Agent': 'Mozilla/5.0'} ,allow_redirects=False)
        html = response.content.decode('latin1')
        extracts = re.findall('href="[https:]*[/{1,2}#]*[\w+.\-/=?_#]*"' ,html)
        fix_links = fix_urls([link.replace('href=', '').replace('"', '') for link in extracts])
        return fix_links
    except:
        return []

def find_information(links):
    relevants = []
    for link in links:
        response = requests.get(link, headers={'User-Agent': 'Mozilla/5.0'}, allow_redirects=False)
        html = response.content.decode('latin1')
        info = re.findall(values_search ,html)
        if info:
            relevants.append(link)
    return relevants


# fix incomplete urls to access active
def fix_urls(links):
    fix_links = []
    for link in links:
        if '?' in link:
            link = link[:link.find('?')]
        if '#' in link:
            link = link[:link.find('#')]
        if link.startswith('//'):
            link = 'https:' + link
        elif link.startswith('/') and len(link) > 1:
            link = 'https://' + root.split('/')[2] + link
        elif not '/' in link:
            link = 'https://' + root.split('/')[2] + '/' + link
        link = link[:-1] if link.endswith('/') else link
        if link:
            fix_links.append(link)
    return fix_links

# create datasets information for each link
def create_datasets(links ,depth):
    datasets = []
    for link in links:
        if not link in visited and not link.split('.')[-1] in ignore:
            dataset = (link ,depth ,try_open_url(link))
            datasets.append(dataset)
            visited.append(link)
    return datasets

# check access to url
def try_open_url(link):
    try:
        access = requests.get(link ,headers={'User-Agent': 'Mozilla/5.0'} ,allow_redirects=False)
        return access.status_code in [200 ,301 ,302 ,303 ,403 ,406 ,500 ,999]
    except:
        return False

# insert urls data to file results
def add_data_to_json(datasets):
    data = read_from_file()
    global serial
    for dataset in datasets:
        link ,depth ,access = dataset[0] ,dataset[1] ,dataset[2]
        key = 'url_' + str(serial)
        value = {
            "path": link,
            "depth": depth,
            "access": access
        }
        data[key] = value
        serial = serial + 1
    write_to_file(data)

# read latest data from file results
def read_from_file():
    with open(file_path , "r") as file:
        if format == 'yaml' or format == 'yml':
            data = yaml.safe_load(file)
        elif format == 'json':
            data = json.load(file)
    return data

# write new data to file results
def write_to_file(data):
    with io.open(file_path, 'w', encoding='utf8') as file:
        if format == 'yaml' or format == 'yml':
            yaml.dump(data, file, default_flow_style=False, allow_unicode=True, sort_keys=False)
        elif format == 'json':
            json.dump(data, file, indent=4)

# download all data from main url up to max depth
def download_urls(links ,depth = 0):
    if depth == max_depth:
        return links
    else:
        print("\nextract urls from " + str(root) + " in depth " + str(depth + 1) + ":")
        bar = progressbar.ProgressBar(max_value=len(links) ,widgets=widgets).start()
        next = 0
        cumulative = []
        for link in links:
            extracts = extract_urls(link)
            # relevants = find_information(extracts)
            datasets = create_datasets(extracts ,depth + 1)
            cumulative = cumulative + datasets
            bar.update(next)
            next = next + 1
        add_data_to_json(cumulative)
        new_links = [dataset[0] for dataset in cumulative]
        return links + download_urls(new_links ,depth + 1)

# main test
if __name__ == "__main__":
    start = datetime.datetime.now()
    access = try_open_url(root)
    create_file_format()
    ignore = get_extension_unnecessaries()
    if access:
        visited.append(root)
        links = download_urls([root])
        assert len(set(links)) == len(links)
    end = datetime.datetime.now()
    print("\nrun time: " + str(end - start))
