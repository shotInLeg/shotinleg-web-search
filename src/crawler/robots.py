# coding: utf8
import lib.network as network


def parse_robot_txt(url):
    params = {
        'Crawl-delay': 1,
        'Disallow': []
    }

    robot_txt = network.get(url, retry=True).text
    for line in robot_txt.split('\n'):
        line = line.strip()

        if not line:
            continue
        elif 'Crawl-delay' in line:
            params['Crawl-delay'] = int(line.split(' ')[-1])
        elif 'Disallow' in line:
            params['Disallow'].append(line.split(' ')[-1])

    return params

