from abc import ABCMeta
from collections import OrderedDict
import re

from lxml import etree
from nltk import word_tokenize
import networkx
import pandas

from utils import window_iter_fill

class BasicLoader():
    __metaclass__ = ABCMeta
    file_location = "/home/siak/pro/projects/leon/data/all-reviews.xml"
    punctuation = '\'!"#$%\()*+,-./:;<=>?@[\\]^_`{|}~'
    end_of_sentence_punctuation = '!.?'

    def remove_names(self, text):
        pattern = re.compile("[" + self.end_of_sentence_punctuation+ "][ ]?[A-Z][a-z]*")
        return re.sub(pattern, ' ', text)

    def remove_punctuation(self, text):
        regex = re.compile('[%s]' % re.escape(self.punctuation))
        return regex.sub(' ', text)

    def tokenize(self, text, split):
        words = word_tokenize(text)
        if not split:
            return ' '.join(words)
        return words

    def get_text(self, root, node_name, process=False):
        text = root.find(node_name).text
        text = ' '.join(text.split('\n'))
        if not process:
            return text
        return self.process_text(text)

    def get_words(self, text, split=False):
        text = self.remove_names(text)
        text = self.remove_punctuation(text)
        return self.tokenize(text, split)


class SingleWordsLoader(BasicLoader):
    def read_dataframe_from_xml(self):
        tree = etree.parse(self.file_location)
        headers = OrderedDict({'review_text': True,
                               'title': True,
                               'rating': False,
                               'product_name': False,
                               'helpful': False,
                               'product_type': False})

        all = []
        for review in tree.iter('review'):
            data = pandas.Series([self.get_text(review, name, process)
                                  for name, process in headers.iteritems()],
                                 index=headers.keys())

            all.append(data)
        return pandas.concat(all, axis=1).transpose()


class BigramLoader(BasicLoader):
    def __init__(self):
        self.graph = networkx.DiGraph()

    def get_sentences(self, text):
        pattern = re.compile("[" + self.end_of_sentence_punctuation + ",]")
        return re.split(pattern, text)

    def initialize_nodes(self, node_names):
        for name in node_names:
            if not self.graph.has_node(name):
                self.graph.add_node(name, weights={'title': [], 'review': []})

    def process_sentence(self, sentence, source, sentiment):
        assert(source in ['review', 'title'])
        words = self.get_words(sentence, split=True)
        gen = window_iter_fill(words, fill="End")
        for word1, word2 in gen:
            self.initialize_nodes([word1, word2])
            self.graph.node[word1]['weights'][source].append(sentiment)
            if not self.graph.has_edge(word1, word2):
                self.graph.add_edge(word1, word2, weights={'title': [], 'review': []})
            self.graph[word1][word2]['weights'][source].append(sentiment)

    def process_text(self, text, source, rating):
        for sentence in self.get_sentences(text):
            self.process_sentence(sentence, source, rating)

    def process_review(self, review):
        rating = (float(review.find('rating').text) - 3) / 2
        text = review.find('review_text').text
        self.process_text(text, 'review', rating)
        title = review.find('title').text
        self.process_text(title, 'title', rating)

    def read_graph_from_xml(self, reviews_number):
        tree = etree.parse(self.file_location)
        for index, review in enumerate(tree.iter('review')):
            if index == reviews_number:
                break
            #commented this bit out for speed up
            #print index
            self.process_review(review)

