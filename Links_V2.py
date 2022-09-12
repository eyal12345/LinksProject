from bs4 import BeautifulSoup # pip install bs4
import requests # pip install requests
import datetime
import sys
import yaml # pip install pyyaml
import json
import io
import xml.etree.ElementTree as ET

# user input
root = sys.argv[1]
max_depth = int(sys.argv[2])
format = sys.argv[3]

# global variables
serial = 1
visited = [root]
file_path = root.split('.')[1] + "_" + str(max_depth) + "." + format

def create_file_format():
    if format == 'yaml' or format == 'yml':
        yaml.dump({}, open(file_path, "w"), default_flow_style=False, allow_unicode=True, sort_keys=False)
    elif format == 'json':
        json.dump({}, open(file_path, "w"), indent=4)
    elif format == 'xml':
        data = ET.Element('data')
        data.text = ''
        b_xml = ET.tostring(data)
        with open(file_path, "wb") as f:
            f.write(b_xml)
    else:
        raise Exception('the format is invalid')

def add_data_to_file(links ,depth):
    result = read_from_file()
    global serial
    for link in links:
        key = 'url_' + str(serial)
        value = {
            "path": link,
            "depth": depth
        }
        result[key] = value
        serial = serial + 1
    write_to_file(result)

def read_from_file():
    with open(file_path , "r") as file:
        if format == 'yaml' or format == 'yml':
            content = yaml.safe_load(file)
        elif format == 'json':
            content = json.load(file)
        elif format == 'xml':
            tree = ET.parse(file_path)
            content = tree.getroot()
    return content

def write_to_file(content):
    with io.open(file_path, 'w', encoding='utf8') as file:
        if format == 'yaml' or format == 'yml':
            yaml.dump(content, file, default_flow_style=False, allow_unicode=True, sort_keys=False)
        elif format == 'json':
            json.dump(content, file, indent=4)
        elif format == 'xml':
            items = ET.SubElement(ET.parse(file_path).getroot(), 'url_' + str(serial))
            for k,v in content.items():
                path = ET.SubElement(items, 'path')
                path.text = 'item1abc'
                depth = ET.SubElement(items, 'depth')
                depth.text = 'item2abc'
            b_xml = ET.tostring(content)
            with open(file_path, "wb") as f:
                f.write(b_xml)

def fix_url(link):
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
    return link

def try_open_url(link):
    try:
        access = requests.get(link ,headers={'User-Agent': 'Mozilla/5.0'} ,allow_redirects=False)
        return access.status_code in [200 ,301 ,302 ,303 ,403 ,406 ,500 ,999]
    except:
        return False

def download_urls(links ,depth = 0):
    add_data_to_file(links ,depth)
    if depth == max_depth:
        return links
    else:
        new_links = []
        for link in links:
            if try_open_url(link):
                response = requests.get(link ,headers={'User-Agent': 'Mozilla/5.0'} ,allow_redirects=False)
                html_page = response.content.decode('latin1')
                soup = BeautifulSoup(html_page, "html.parser")
                for comp in soup.findAll('a'):
                    url = comp.get('href')
                    if url and url.startswith('https'):
                        url = fix_url(url)
                        if not url in visited:
                            new_links.append(url)
                            visited.append(url)
        return links + download_urls(new_links ,depth + 1)

start = datetime.datetime.now()
create_file_format()
links = download_urls([root])
assert len(set(links)) == len(links)
end = datetime.datetime.now()
print("\nrun time: " + str(end - start))
