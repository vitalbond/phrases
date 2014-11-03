from __future__ import division
import nltk, os, sys, re, getopt, time
from nltk.probability import FreqDist
from HTMLParser import HTMLParser


def gmean(nums):
    return (reduce(lambda x, y: x*y, nums))**(1.0/len(nums))


def strip_tags(html):
    result = []
    parser = HTMLParser()
    parser.handle_data = result.append
    parser.feed(html)
    parser.close()
    return ' '.join(result)


_re_non_punct = re.compile(r'[^\W\d]', re.UNICODE)
def is_punct(w):
    return not _re_non_punct.search(w)


_english_stopwords = set(nltk.corpus.stopwords.words('english'))
_non_english_stopwords = set(nltk.corpus.stopwords.words())-_english_stopwords
def is_stopword(w):
    return is_punct(w) or is_quote_token(w) or w.lower() in _english_stopwords


_quote_token_re = re.compile(r"^('[sS]|'[mM]|'[dD]|'ll|'LL|'re|'RE|'ve|'VE|n't|N'T')$")
def is_quote_token(w):
    return _quote_token_re.match(w)


def get_corpus_words_fd():
    corpus = nltk.corpus.gutenberg
    tokens = []
    for text in corpus.fileids():
        tokens+=[w.lower() for w in corpus.words(text)]
        # w in nltk.word_tokenize(corpus.raw(text))

    return FreqDist(tokens)


def get_words_fd(documents):
    fd = FreqDist()
    for document in documents:
        for word in document:
            fd[word.lower()] += 1
    return fd


_wfr_cache = {}
def wfr_clear_cache():
    global _wfr_cache
    _wfr_cache = {}


def word_freq_ratio(w, words_fd):
    global _wfr_cache
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


def phrase_output(words):
    if not len(words):
        return ''
    phrase = words[0]
    for w in words[1:]:
        if not _quote_token_re.match(w):
            phrase+=' '
        phrase+=w
    return phrase


def find_phrases(documents, maxLength, count, min_doc_freq=0.03):
    documents_count = len(documents)
    phrases = []
    words_fd = get_words_fd(documents)

    for N in range(2, maxLength+1):
        ngram_counter = {}

        for document in documents:
            ngrams_in_document = {}
            for ng in nltk.ngrams(document, N):
                ng_lower = tuple([w.lower() for w in ng])
                if not is_stopword(ng_lower[0]) and not  is_stopword(ng_lower[-1]) and not any(is_punct(w) for w in ng_lower):
                    if not ng_lower in ngram_counter:
                        ngram_counter[ng_lower] = [0, 0, ng]
                    ngram_counter[ng_lower][0] += 1
                    ngrams_in_document[ng_lower] = 1

            for ng in ngrams_in_document.keys():
                ngram_counter[ng][1] += 1


        for ng in ngram_counter:
            #filter by document frequency
            if ngram_counter[ng][1]/documents_count<min_doc_freq:
                continue

            word_freq_ratios = []
            for w in ng:
                wfr = word_freq_ratio(w, words_fd)
                if wfr:
                    word_freq_ratios.append(wfr)

            phrase_value = gmean(word_freq_ratios)

            #filter by phrase value
            if phrase_value<15:
                continue

            phrases.append((ngram_counter[ng][2], ngram_counter[ng][0], N, ngram_counter[ng][0]*(N+2), ngram_counter[ng][1]*(N+2), phrase_value))

    if not phrases:
        return []

    phrases_filtered = []
    for i in xrange(0, len(phrases)):
        ok = True
        for j in xrange(i+1, len(phrases)):
            if phrases[i][1]*0.9<=phrases[j][1] and phrases[i][2]<phrases[j][2]:
                for k in xrange(0, phrases[j][2]-phrases[i][2]+1):
                    if (phrases[i][0]==phrases[j][0][k:k+phrases[i][2]]):
                        ok = False
                        break
        if ok:
            phrases_filtered.append(phrases[i])

    phrases = phrases_filtered

    max_freq = max([x[3] for x in phrases])
    max_freq_docs = max([x[4] for x in phrases])
    max_value = max([x[5] for x in phrases])

    #rank
    phrases_ranked = [(x[0], 0.5*x[4]/max_freq_docs+0.3*x[3]/max_freq+0.2*x[5]/max_value, x[4], x[3], x[5]) for x in phrases]

    #sort & limit
    phrases_sorted = sorted(phrases_ranked, key=lambda t: -t[1])[:count]

    return phrases_sorted


def process_dir(dir, opts):
    global time_search, time_load
    documents = []
    tokens_set = set()
    wfr_clear_cache()

    time_load-=time.time()
    for f in os.listdir(dir):
        file = os.path.join(dir, f)
        if os.path.isfile(file):
            str = strip_tags(open(file, 'r').read().decode('utf-8'))
            tokens = nltk.word_tokenize(str)
            tokens = [w for w in tokens]
            tokens_set = tokens_set.union(tokens)
            documents.append(tokens)
    time_load+=time.time()

    if len(tokens_set & _english_stopwords) <= len(tokens_set & _non_english_stopwords):
        print "Not english text"
        return

    time_search-=time.time()
    phrases = find_phrases(documents, maxLength=maxLength, count=count)
    time_search+=time.time()

    for x in phrases:
        print phrase_output(x[0]) + (' %0.2f (%0.2f, %0.2f, %0.2f)' % (x[1], x[2], x[3], x[4]) if '--v' in opts else '')


try:
    opts, args = getopt.getopt(sys.argv[1:], '', ['dir=', 'count==', 'maxLength==', 'subdirs', 'v'])
except getopt.GetoptError as err:
    print('python phrases.py --dir=dir [--count=20] [--maxLength=6] [--v] [--subdirs]')
    exit()

opts = dict(opts)

dir = opts['--dir']
maxLength = int(opts['--maxLength=']) if '--maxLength=' in opts else 6
count = int(opts['--count=']) if '--count=' in opts else 20

if not os.path.isdir(dir):
    print("Dir not exists")
    exit()

time_corpus = -time.time()
corpus_words_fd = get_corpus_words_fd()
time_corpus += time.time()

time_load = time_search = 0

if '--subdirs' in opts:
    for f in os.listdir(dir):
        path = os.path.join(dir, f)
        if os.path.isdir(path):
            print f+':'
            process_dir(path, opts)
            print "\n"
else:
    process_dir(dir, opts)

print "Load corpus: %0.2f sec" % time_corpus
print "Load texts: %0.2f sec" % (time_load)
print "Search phrases: %0.2f sec" % (time_search)