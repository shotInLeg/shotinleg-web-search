#!/usr/bin/env python
# coding: utf8
import os
import sys
import json
import argparse
import hashlib
import multiprocessing

import flask

from flask import Flask
from nltk.stem.cistem import Cistem



APP = Flask(__name__)
stemmer = Cistem()


def arg_parser():
    def list_comma_str(values):
        return [x.strip() for x in values.split(',') if x.strip()]

    parser = argparse.ArgumentParser(
        description='shotinleg-web-search: simple gui for web seacrh.'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=80,
        help='Port for start.'
    )
    parser.add_argument(
        '--data-path',
        type=str,
        default='../data',
        help='Path to data.'
    )

    return  parser.parse_args()


class Index(object):
    m = multiprocessing.Manager()
    index = m.dict()
    data_path = ''

    @staticmethod
    def load(data_path, filename):
        with open(os.path.join(data_path, filename)) as rfile:
            Index.index = Index.m.dict(json.load(rfile))
        Index.data_path = data_path

    @staticmethod
    def get_links_by_words(words):
        links = {}
        for word in words:
            word = stemmer.stem(word)

            print('{}'.format(word))

            data = Index.index.get(word, {})

            print(data, len(Index.index))

            for link in data:
                if link not in links:
                    links[link] = 0
                links[link] += data[link]

        return sorted(links, key=lambda x: links[x], reverse=True)

    @staticmethod
    def info_by_link(link):
        hash_name = hashlib.md5(link.encode('utf-8')).hexdigest()
        with open(os.path.join(Index.data_path, '{}.json'.format(hash_name))) as rfile:
            data = json.load(rfile)

        return str(data['title']), str(data['url'])


@APP.route('/')
def morda():
    return flask.render_template('index.html')


@APP.route('/search')
def search():
    q = flask.request.args.get('q', '').strip()
    links = Index.get_links_by_words(q.split(' '))
    prepared = []
    for link in links:
        title, url = Index.info_by_link(link)
        prepared.append({
            'title': title,
            'url': url
        })
    return flask.render_template('search.html', links=prepared, query=q)


def websearch(port, data_path):
    Index.load(data_path, 'index.json')
    APP.run(host='::', port=port, debug=True)



def main(port, data_path):
    websearch(port, data_path)
    return 0


if __name__ == '__main__':
    args = arg_parser()
    ret_value = main(args.port, args.data_path)
    sys.exit(ret_value)

