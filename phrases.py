from __future__ import division
import nltk, os, sys, re
from nltk.probability import FreqDist
from HTMLParser import HTMLParser



def sqmean(nums):
    return (sum([x*x for x in nums])/len(nums))**0.5


def hmean(nums):
    return 1/sum([1/x for x in nums])


def gmean(nums):
    return (reduce(lambda x, y: x*y, nums))**(1.0/len(nums))


def amean(nums):
    return sum(nums)/len(nums)


class bcolors:
    blue = '\033[94m'
    green = '\033[92m'
    yellow = '\033[93m'
    red = '\033[91m'
    ENDC = '\033[0m'


def colored(str, color):
    return (getattr(bcolors, color) + str + bcolors.ENDC) if color else str


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

def find_phrases(documents, N=2, count=10):
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

    ngs = [(ng, ngram_counter[ng][0], ngram_counter[ng][1]) for ng in ngram_counter]
    ngs_best = sorted(ngs, key=lambda t: (-t[2], -t[1]))[:count]
    return ngs_best


print "\n"

if len(sys.argv) > 1:
    dir = sys.argv[1]
    if not os.path.isdir(dir):
        print("Dir not exists")
        exit()
else:
    print("Dir is not set")
    exit()

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


if len(tokens_set & _english_stopwords) <= len(tokens_set & _non_english_stopwords):
    print("Not english text")
    exit()


corpus_words_fd = get_corpus_words_fd()
words_fd = get_words_fd(documents)
def word_ratio(w):
    if is_stopword(w):
        return 0
    a = words_fd.freq(w)
    b = corpus_words_fd.freq(w)
    if b==0:
        b = 1/corpus_words_fd.N()
    return a/b


for N in [2, 3, 4, 5, 6]:
    ngrams = find_phrases(documents, N=N, count=20)
    print("--- N=%d ---" % (N))
    for x in ngrams:
        word_ratios = [word_ratio(w) for w in x[0] if word_ratio(w)]
        gm = gmean(word_ratios)
        sqm = sqmean(word_ratios)

        bad_symptoms = (gm<15)
        colors = ['', 'red']

        str = colored(' '.join(x[0]), colors[bad_symptoms])
        str += ' [%d/%d]' % (x[1], x[2])
        str += ' ('
        str += ' '.join(['%0.2f' % x for x in word_ratios])
        str += ')'

        str += '%0.2f ' % gm
        str += '%0.2f ' % sqm

        print str

print "\n"