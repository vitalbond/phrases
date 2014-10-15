from __future__ import division
import nltk, os, sys
from HTMLParser import HTMLParser
import itertools as _itertools


def strip_tags(html):
    result = []
    parser = HTMLParser()
    parser.handle_data = result.append
    parser.feed(html)
    parser.close()
    return ''.join(result)


def find_phrases(documents, finders):
    ignored_words = nltk.corpus.stopwords.words('english')

    for finder in finders:
        f = finder['finder']
        f = f.from_documents(documents)

        f.apply_word_filter(lambda w: len(w) < 3 or w.lower() in ignored_words)
        f.apply_freq_filter(finder['freq_min'])

        ngrams = f.score_ngrams(getattr(finder['measures'], finder['measure']))[:20]

        print("--- %s ---" % finder['measure'])
        print("\n".join([' '.join(x[0]) + (' [%02f]' % x[1]) for x in ngrams]))
    print("\n")


if len(sys.argv) > 1:
    dir = sys.argv[1]
    if not os.path.isdir(dir):
        print("Dir not exists")
        exit()
else:
    print("Dir is not set")
    exit()

documents = []
for f in os.listdir(dir):
    file = os.path.join(dir, f)
    if os.path.isfile(file):
        str = strip_tags(open(file, 'r').read()).decode('utf-8')
        tokens = nltk.word_tokenize(str)
        documents.append(tokens)

#finders = [{'finder': nltk.BigramCollocationFinder, 'measures': nltk.metrics.association.BigramAssocMeasures(), 'measure': 'likelihood_ratio', 'freq_min': 10}]
#finders += [{'finder': nltk.TrigramCollocationFinder, 'measures': nltk.metrics.association.TrigramAssocMeasures(), 'measure': 'likelihood_ratio', 'freq_min': 5}]
#finders += [{'finder': nltk.QuadgramCollocationFinder, 'measures': nltk.metrics.association.QuadgramAssocMeasures(), 'measure': 'likelihood_ratio', 'freq_min': 3}]

ngram = 'Bigram'

measures = ["raw_freq"]
finders = [{'finder': getattr(nltk, ngram + 'CollocationFinder'), 'measures': getattr(nltk.metrics.association, ngram + 'AssocMeasures')(), 'measure': x, 'freq_min': 10} for x in measures]

find_phrases(documents, finders)

