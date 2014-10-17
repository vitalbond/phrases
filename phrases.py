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



def find_phrases(documents, N=2, measure='raw_freq', words_filter = 'default', window_size = 0, freq_min = 0):
    if N==2:
        ngram = 'Bigram'
    elif N==3:
        ngram = 'Trigram'
    elif N==4:
        ngram = 'Quadgram'
    else:
        raise Exception("wrong N: %d" % N)

    window_size += N

    finder = getattr(nltk, ngram + 'CollocationFinder')

    ngram_documents_fd = FreqDist()
    ngram_fd = FreqDist()
    for document in documents:

        print "\n"
        print document

        finder = finder.from_words(document)

        if words_filter=='default':
            finder.apply_word_filter(lambda w: is_punct(w))
            finder.apply_ngram_filter(lambda *ngram: is_stopword(ngram[0]) or is_stopword(ngram[-1]))
        elif words_filter=='punct':
            finder.apply_word_filter(lambda w: is_punct(w))
        elif words_filter=='stopwords':
            finder.apply_word_filter(is_stopword)

        ngs = finder.ngram_fd

        print "\n"
        print [item for item in ngs.iteritems()]

        for ng in ngrams(document, N):
            if not is_stopword(ng[0]) and not  is_stopword(ng[-1]) and not any(is_punct(w) for w in ng):
                ngram_fd[ng] += item[1]
                ngram_documents_fd[item[0]] += 1

    return

    print "\n"
    print [item for item in ngram_fd.iteritems()]
    print "\n"
    print [item for item in ngram_documents_fd.iteritems()]

    return

    measure_obj = getattr(getattr(nltk.metrics.association, ngram + 'AssocMeasures')(), measure)

    if freq_min:
        finder.apply_freq_filter(freq_min)

    #ngrams = finder.ngram_fd

    print "\n"
    #print [item for item in ngrams.iteritems()]
    print "\n"

    ngrams_scored = finder.score_ngrams(measure_obj)[:10]

    print("--- N=%d measure=%s filter=%s ---" % (N, measure, words_filter))
    print("\n".join([' '.join(x[0]) + (' [%02f]' % x[1]) for x in ngrams_scored]))


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

for N in [3]:
    find_phrases(documents, N=N, measure="raw_freq", freq_min=0, words_filter="default")

print "\n"

