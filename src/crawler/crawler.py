#!/usr/bin/env python
# coding: utf8
import re
import os
import sys
import json
import time
import hashlib
import argparse
import datetime

import lib.network as network

from bs4 import BeautifulSoup


DOMAIN = re.compile(r'http[s]{0,1}://(?P<domain>[A-Za-z0-9.-]+)/*')


def parse_html_page(html):
    soup = BeautifulSoup(html, 'html.parser')

    title = soup.title.text if soup.title else ''

    headers = [h.text.strip() for h in soup.findAll('h1') if h.text.strip()]
    headers.extend([h.text.strip() for h in soup.findAll('h2') if h.text.strip()])
    headers.extend([h.text.strip() for h in soup.findAll('h3') if h.text.strip()])

    links = set()
    for i in soup.find_all('a', href=True):
        links.add(i['href'])

    return title, headers, links


def get_site_from_url(url):
    m = DOMAIN.match(url)
    if m:
        return m.groupdict()['domain']
    return url


def normilize_links(links, url, only_current_doman=False):
    site = get_site_from_url(url)

    normilized = set()
    for link in links:
        if site is not None and '//:{}'.format(site) in link:
            normilized.add(link)
        elif link.startswith('http') and not only_current_doman:
            normilized.add(link)
        elif site is not None and link.startswith('/'):
            normilized.add('http://{}{}'.format(site, link))
        elif url is not None and not link.startswith('/') and not link.startswith('http'):
            normilized.add('{}{}'.format(url, link))
    return normilized


def crawler(urls, output_path, visited_urls=None, downloaded=None, depth=None):
    if depth is not None:
        if depth <= 0:
            return
        depth -= 1

    visited_urls = visited_urls or set()
    downloaded = downloaded or {}
    delay = 6  # TODO: Add robots.txt

    next_step_links = set()
    for i, url in enumerate(urls):
        if url in visited_urls:
            continue

        try:
            html = network.get_html_page(url, retry=True)
            title, headers, links = parse_html_page(html)
            links = normilize_links(links, url, only_current_doman=True)
        except Exception as e:
            print('[SKIP] {}, because {}'.format(url, e))
            continue

        next_step_links |= {x for x in links if x not in visited_urls}

        filename = hashlib.md5(url.encode('utf-8')).hexdigest()
        with open(os.path.join(output_path, '{}.json'.format(filename)), 'w') as wfile:
            data = {
                'url': url,
                'title': title,
                'headers': headers,
                'html': html,
                'links': list(links)
            }
            wfile.write(json.dumps(data, indent=4))
        downloaded[url] = {
            'url': url,
            'path': os.path.join(output_path, '{}.json'.format(filename)),
            'links': list(links)
        }

        visited_urls.add(url)
        print('[{}] Sleep {}s ({}/{})'.format(datetime.datetime.now().strftime("%H:%M:%S"), delay, i, len(urls)))
        time.sleep(delay)

    with open(os.path.join(output_path, 'downloaded.json'), 'w') as wfile:
        wfile.write(json.dumps(downloaded, indent=4))

    print('[{}] Sleep 10s (depth: {})'.format(datetime.datetime.now().strftime("%H:%M:%S"), depth))
    time.sleep(10)

    if next_step_links:
        crawler(next_step_links, output_path, visited_urls, downloaded, depth)


def arg_parser():
    def list_comma_str(values):
        return [x.strip() for x in values.split(',') if x.strip()]

    parser = argparse.ArgumentParser(
        description='shotinleg-crawler: simple http crawler for html pages.'
    )
    parser.add_argument(
        '--start-urls',
        type=list_comma_str,
        required=True,
        help='List of start crawler urls.'
    )
    parser.add_argument(
        '--depth',
        type=int,
        default=None,
        help='Optional. Max depth for test run.'
    )

    return  parser.parse_args()


def main(start_urls, depth):
    crawler(start_urls, 'data', depth=depth)
    return 0


if __name__ == '__main__':
    args = arg_parser()
    ret_value = main(args.start_urls, args.depth)
    sys.exit(ret_value)

