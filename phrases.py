from __future__ import division
import nltk, os, sys, re
from HTMLParser import HTMLParser
import itertools as _itertools
from nltk.compat import iteritems
from nltk.probability import FreqDist
from nltk.util import ngrams

def strip_tags(html):
    result = []
    parser = HTMLParser()
    parser.handle_data = result.append
    parser.feed(html)
    parser.close()
    return ''.join(result)


_re_non_punct = re.compile(r'[^\W\d]', re.UNICODE)
def is_punct(w):
    return not _re_non_punct.search(w)


_stopwords = nltk.corpus.stopwords.words('english')
def is_stopword(w):
    return len(w) < 3 or w.lower() in _stopwords



def find_phrases(documents, N=2):
    L = len(documents)
    ngram_counter = {}
    for document in documents:
        ngrams_in_document = {}
        for ng in ngrams(document, N):
            if not is_stopword(ng[0]) and not  is_stopword(ng[-1]) and not any(is_punct(w) for w in ng):
                if not ng in ngram_counter:
                    ngram_counter[ng] = [0, 0]
                ngram_counter[ng][0] += 1
                ngrams_in_document[ng] = 1

        for ng in ngrams_in_document.keys():
            ngram_counter[ng][1] += 1

    ngs = [(ng, ngram_counter[ng][0], ngram_counter[ng][1]) for ng in ngram_counter]
    ngs_best = sorted(ngs, key=lambda t: (-t[1], -t[2]))[:10]

    print("--- N=%d ---" % (N))
    print("\n".join([' '.join(x[0]) + (' [%d/%d]' % (x[1], x[2])) for x in ngs_best]))


if len(sys.argv) > 1:
    dir = sys.argv[1]
    if not os.path.isdir(dir):
        print("Dir not exists")
        exit()
else:
    print("Dir is not set")
    exit()

print "\n"

documents = []
for f in os.listdir(dir):
    file = os.path.join(dir, f)
    if os.path.isfile(file):
        str = strip_tags(open(file, 'r').read()).decode('utf-8')
        #print str
        tokens = nltk.word_tokenize(str)
        tokens = [w.lower() for w in tokens]
        documents.append(tokens)


#raw_freq
#student_t
#chi_sq
#mi_like
#pmi
#likelihood_ratio
#poisson_stirling
#jaccard

for N in [2, 3, 4]:
    find_phrases(documents, N=N)

print "\n"

