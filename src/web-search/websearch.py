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
from bs4 import BeautifulSoup
from bs4.element import Comment
from nltk.stem.snowball import SnowballStemmer


APP = Flask(__name__)
stemmer = SnowballStemmer('russian')


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
    def get_links_by_query(query):
        links = {}
        for word in Index.simplify_query(query):
            data = Index.index.get(word, {})

            for link in data:
                if link not in links:
                    links[link] = 0
                links[link] += data[link]

        return sorted(links, key=lambda x: links[x], reverse=True)

    @staticmethod
    def simplify_query(query):
        bag_of_words = [x.strip() for x in query.split(' ') if x.strip()]
        return [stemmer.stem(x) for x in bag_of_words]

    @staticmethod
    def text_from_tags(html, skip_tags):
        def tag_visible(element):
            if element.parent.name in skip_tags:
                return False
            if isinstance(element, Comment):
                return False
            return True

        soup = BeautifulSoup(html, 'html.parser')
        texts = soup.findAll(text=True)
        visible_texts = filter(tag_visible, texts)
        text = " ".join(t.strip() for t in visible_texts)

        return text

    @staticmethod
    def snippet_by_html(html, query):
        text_from_page = Index.text_from_tags(html, ['style', 'script', 'head', 'title', 'meta', '[document]', 'a', 'button'])

        snippets = []
        for seq in text_from_page.split('. '):
            if not seq:
                continue

            count = 0
            for word in Index.simplify_query(query):
                if word in Index.simplify_query(seq):
                    count += 1
            snippets.append((seq, count))
        snippets = [x[0] for x in sorted(snippets, key=lambda x: x[1], reverse=True)]

        return '. '.format(snippets[:2])

    @staticmethod
    def info_by_link(link, query):
        hash_name = hashlib.md5(link.encode('utf-8')).hexdigest()
        with open(os.path.join(Index.data_path, '{}.json'.format(hash_name))) as rfile:
            data = json.load(rfile)
        snippet = Index.snippet_by_html(data['html'], query)

        return str(data['title']), str(data['url']), snippet


@APP.route('/')
def morda():
    return flask.render_template('index.html')


@APP.route('/search')
def search():
    q = flask.request.args.get('q', '').strip()
    links = Index.get_links_by_query(q)
    prepared = []
    for link in links:
        title, url, snippet = Index.info_by_link(link, q)
        prepared.append({
            'title': title,
            'url': url,
            'snippet': snippet
        })
    return flask.render_template('search.html', links=prepared, query=q)


@APP.route('/about')
def about():
    return flask.render_template('about.html')


def websearch(port, data_path):
    Index.load(data_path, 'index.json')
    APP.run(host='::', port=port, debug=True)


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


def main(port, data_path):
    websearch(port, data_path)
    return 0


if __name__ == '__main__':
    args = arg_parser()
    ret_value = main(args.port, args.data_path)
    sys.exit(ret_value)

