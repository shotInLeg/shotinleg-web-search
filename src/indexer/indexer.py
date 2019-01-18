#!/usr/bin/env python
# coding: utf8
import os
import sys
import json
import time
import argparse
import functools
import collections

from bs4 import BeautifulSoup
from bs4.element import Comment
from nltk.stem.snowball import SnowballStemmer


stemmer = SnowballStemmer('russian')



def worktime(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print('[WORKTIME] {} by {}s'.format(func.__name__, time.time() - start))
        return result
    return wrapper


@worktime
def parse_html_page(html):
    def tag_visible(element):
        if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
            return False
        if isinstance(element, Comment):
            return False
        return True

    soup = BeautifulSoup(html, 'html.parser')
    title = soup.title.text if soup.title else ''
    headers = [h.text.strip() for h in soup.findAll('h1') if h.text.strip()]
    headers.extend([h.text.strip() for h in soup.findAll('h2') if h.text.strip()])
    headers.extend([h.text.strip() for h in soup.findAll('h3') if h.text.strip()])

    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)
    text = " ".join(t.strip() for t in visible_texts)

    links = set()
    for i in soup.find_all('a', href=True):
        links.add(i['href'])

    return title, headers, text, links


@worktime
def bag_of_words(text):
    return [x.strip() for x in text.replace('\n', ' ').split(' ') if x.strip()]


@worktime
def steming(bag_of_words_data):
    return [stemmer.stem(x) for x in bag_of_words_data]


@worktime
def count_words(words):
    def is_in_dict(dct, key):
        try:
            _ = dct[key]
        except KeyError:
            return False
        return True

    print('    words: {}'.format(len(words)))
    words_count = {}
    for word in words:
        if not is_in_dict(words_count, word):
            words_count[word] = 0
        words_count[word] += 1
    return words_count


@worktime
def update_index(words_count, index, url, k):
    for word, count in words_count.items():
        if word not in index:
            index[word] = {}
        index[word][url] = count * k


def indexer(downloaded_path, output_path):
    with open(downloaded_path, 'r') as rfile:
        downloaded = json.load(rfile)

    with open(os.path.join(output_path, 'index.json')) as rfile:
        try:
            old_index = json.load(rfile)
            visited_links = set()
            for _, data in old_index.items():
                for link in data:
                    visited_links.add(link)
        except Exception:
            visited_links = set()

    index = {}
    for i, (url, data) in enumerate(downloaded.items()):
        if url in visited_links:
            continue

        with open(data['path']) as rfile:
            page = json.load(rfile)

        _, _, text, _ = parse_html_page(page['html'])
        words = bag_of_words(text)
        words = steming(words)

        header_words = []
        for header in page['headers']:
            header_words.extend(bag_of_words(header))
        header_words = steming(header_words)

        title_words = bag_of_words(page['title'])
        title_words = steming(title_words)

        words_count = count_words(words)
        header_words_count = count_words(header_words)
        title_words_count = count_words(title_words)

        update_index(words_count, index, url, 1)
        update_index(header_words_count, index, url, 100)
        update_index(title_words_count, index, url, 200)

        print('Processed {} ({}/{})'.format(url, i, len(downloaded)))

        if i and i % 10 == 0 and output_path:
            try:
                json_data = json.dumps(index, indent=4)
                with open(os.path.join(output_path, 'index.json'), 'w') as wfile:
                    wfile.write(json_data)
                with open(os.path.join(output_path, 'index2.json'), 'w') as wfile:
                    wfile.write(json_data)
            except Exception as e:
                print('[ERROR] {}: {}'.format(type(e), e))

            print('Flushed {} urls to index'.format(i))

    if output_path is not None:
        json_data = json.dumps(index, indent=4)
        with open(os.path.join(output_path, 'index.json'), 'w') as wfile:
            wfile.write(json_data)

    return index


def arg_parser():
    parser = argparse.ArgumentParser(
        description='shotinleg-indexer: simple indexer for html pages.'
    )
    parser.add_argument(
        '--downloaded-path',
        type=str,
        required=True,
        help='Path of downloaded.json'
    )

    return  parser.parse_args()


def main(downloaded_path):
    indexer(downloaded_path)
    return 0


if __name__ == '__main__':
    args = arg_parser()
    ret_value = main(args.downloaded_path)
    sys.exit(ret_value)

