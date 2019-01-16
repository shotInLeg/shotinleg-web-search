#!/usr/bin/env python
# coding: utf8
import os
import sys
import json
import argparse
import collections

from nltk.stem.cistem import Cistem


stemmer = Cistem()


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


def bag_of_words(text):
    return [x.strip() for x in text.replace('\n', ' ').split(' ') if x.strip()]


def steming(bag_of_words_data):
    return [stemmer.stem(x) for x in bag_of_words_data]


def count_words(words):
    words_count = collections.defaultdict(int)
    for uniq_word in set(words):
        words_count[uniq_word] = words.count(uniq_word)
    return words_count


def indexer(downloaded_path, output_path):
    with open(downloaded_path, 'r') as rfile:
        downloaded = json.load(rfile)

    index = {}
    for url, data in downloaded.items():
        with open(data['path']) as rfile:
            page = json.load(rfile)
            words = bag_of_words(page['text'])
            words = steming(words)
            header_words = []
            for header in page['headers']:
                header_words.extend(bag_of_words(header))
            header_words = steming(header_words)

            words_count = count_words(words)
            header_words_count = count_words(header_words)

            for word, count in words_count.items():
                if word not in index:
                    index[word] = {}
                index[word][url] = count

            for word, count in header_words.items():
                if word not in index:
                    index[word] = {}
                index[word][url] = count * 100

    if output_path is not None:
        with open(os.path.join(output_path, 'index.json'), 'w') as wfile:
            wfile.write(json.dumps(index, indent=4))

    return index


def main(downloaded_path):
    indexer(downloaded_path)
    return 0


if __name__ == '__main__':
    args = arg_parser()
    ret_value = main(args.downloaded_path)
    sys.exit(ret_value)
