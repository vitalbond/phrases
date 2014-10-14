from __future__ import division
import nltk, os, sys
from HTMLParser import HTMLParser

def strip_tags(html):
    result = []
    parser = HTMLParser()
    parser.handle_data = result.append
    parser.feed(html)
    parser.close()
    return ''.join(result)

if len(sys.argv)>1:
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

finders = [[nltk.BigramCollocationFinder, nltk.metrics.association.BigramAssocMeasures().likelihood_ratio, 10]]
finders += [[nltk.TrigramCollocationFinder, nltk.metrics.association.TrigramAssocMeasures().likelihood_ratio, 5]]
finders += [[nltk.QuadgramCollocationFinder, nltk.metrics.association.QuadgramAssocMeasures().likelihood_ratio, 3]]

ignored_words = nltk.corpus.stopwords.words('english')

for finder in finders:
    freq_filter = finder[2]
    ngram_measure = finder[1]
    finder = finder[0]
    finder = finder.from_documents(documents)
    finder.apply_word_filter(lambda w: len(w) < 3 or w.lower() in ignored_words)
    finder.apply_freq_filter(freq_filter)

    ngrams = finder.nbest(ngram_measure, 20)

    print("---")
    print("\n".join([' '.join(x) for x in ngrams]))

print("\n")