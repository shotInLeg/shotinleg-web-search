#!/usr/bin/env python
# coding: utf8
import os
import sys
import json
import argparse
import collections

from bs4.element import Comment
from nltk.stem.snowball import SnowballStemmer


stemmer = SnowballStemmer('russian')


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


def bag_of_words(text):
    return [x.strip() for x in text.replace('\n', ' ').split(' ') if x.strip()]


def steming(bag_of_words_data):
    return [stemmer.stem(x) for x in bag_of_words_data]


def count_words(words):
    words_count = collections.defaultdict(int)
    for uniq_word in set(words):
        words_count[uniq_word] = words.count(uniq_word)
    return words_count


def update_index(words_count, index, url, k):
    for word, count in words_count.items():
        if word not in index:
            index[word] = {}
        index[word][url] = count * k


def indexer(downloaded_path, output_path):
    with open(downloaded_path, 'r') as rfile:
        downloaded = json.load(rfile)

    index = {}
    for url, data in downloaded.items():
        with open(data['path']) as rfile:
            page = json.load(rfile)

        text = parse_html_page(page['html'])
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

    if output_path is not None:
        with open(os.path.join(output_path, 'index.json'), 'w') as wfile:
            wfile.write(json.dumps(index, indent=4))

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

