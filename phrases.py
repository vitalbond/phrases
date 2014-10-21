from __future__ import division
import nltk, os, sys, re, getopt, time
from nltk.probability import FreqDist
from HTMLParser import HTMLParser


def sqmean(nums):
    return (sum([x*x for x in nums])/len(nums))**0.5


def gmean(nums):
    return (reduce(lambda x, y: x*y, nums))**(1.0/len(nums))


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


_english_stopwords = set(nltk.corpus.stopwords.words('english'))
_non_english_stopwords = set(nltk.corpus.stopwords.words())-_english_stopwords
def is_stopword(w):
    return is_punct(w) or w.lower() in _english_stopwords


def get_corpus_words_fd():
    fd = FreqDist()
    for text in nltk.corpus.gutenberg.fileids():
        for word in nltk.corpus.gutenberg.words(text):
            fd[word] += 1
        #break
    return fd


def get_words_fd(documents):
    fd = FreqDist()
    for document in documents:
        for word in document:
            fd[word] += 1
    return fd


_wfr_cache = {}
def word_freq_ratio(w):
    if w in _wfr_cache:
        return _wfr_cache[w]

    if is_stopword(w):
        _wfr_cache[w] = 0
        return 0
    a = words_fd.freq(w)
    b = corpus_words_fd.freq(w)
    if b==0:
        b = 1/corpus_words_fd.N()

    _wfr_cache[w] = a/b
    return _wfr_cache[w]


def find_phrases(documents, maxLength, count, min_doc_freq=0.04):
    documents_count = len(documents)
    phrases = []

    for N in range(2, maxLength+1):
        ngram_counter = {}

        for document in documents:
            ngrams_in_document = {}
            for ng in nltk.ngrams(document, N):
                if not is_stopword(ng[0]) and not  is_stopword(ng[-1]) and not any(is_punct(w) for w in ng):
                    if not ng in ngram_counter:
                        ngram_counter[ng] = [0, 0]
                    ngram_counter[ng][0] += 1
                    ngrams_in_document[ng] = 1

            for ng in ngrams_in_document.keys():
                ngram_counter[ng][1] += 1



        for ng in ngram_counter:
            #filter
            if ngram_counter[ng][1]/documents_count<min_doc_freq:
                continue

            word_freq_ratios = []
            for w in ng:
                wfr = word_freq_ratio(w)
                if wfr:
                    word_freq_ratios.append(wfr)

            gm = gmean(word_freq_ratios)

            #filter
            if gm<15:
                continue

            sqm = sqmean(word_freq_ratios)
            phrases.append((ng, ngram_counter[ng][0]*N, ngram_counter[ng][1]*N, gm, sqm))

    max_freq = max([x[1] for x in phrases])
    max_freq_docs = max([x[2] for x in phrases])
    max_value = max([x[4] for x in phrases])

    #rank
    phrases_ranked = [(x[0], 0.6*x[2]/max_freq_docs+0.3*x[1]/max_freq+0.1*x[4]/max_value) for x in phrases]

    #sort
    phrases_sorted = sorted(phrases_ranked, key=lambda t: -t[1])[:count]

    return phrases_sorted


try:
    opts, args = getopt.getopt(sys.argv[1:], '', ['dir=', 'count==', 'maxLength=='])
except getopt.GetoptError as err:
    print('python phrases.py --dir=dir --count=20 --maxLength=6')
    exit()

opts = dict(opts)

dir = opts['--dir']
maxLength = int(opts['--maxLength=']) if '--maxLength=' in opts else 6
count = int(opts['--count=']) if '--count=' in opts else 20

if not os.path.isdir(dir):
    print("Dir not exists")
    exit()

time_start = time.time()

documents = []
tokens_set = set()
for f in os.listdir(dir):
    file = os.path.join(dir, f)
    if os.path.isfile(file):
        str = strip_tags(open(file, 'r').read()).decode('utf-8')
        tokens = nltk.word_tokenize(str)
        tokens = [w.lower() for w in tokens]
        tokens_set = tokens_set.union(tokens)
        documents.append(tokens)

time_load = time.time()

if len(tokens_set & _english_stopwords) <= len(tokens_set & _non_english_stopwords):
    print("Not english text")
    exit()

time_corpus = -time.time()
corpus_words_fd = get_corpus_words_fd()
time_corpus += time.time()

words_fd = get_words_fd(documents)
phrases = find_phrases(documents, maxLength=maxLength, count=count)

time_end = time.time()

print "\n"

for x in phrases:
    print ' '.join(x[0])

print "\n"
print "Load corpus: %0.2f sec" % time_corpus
print "Load texts: %0.2f sec" % (time_load-time_start)
print "Search phrases: %0.2f sec" % (time_end-time_load-time_corpus)