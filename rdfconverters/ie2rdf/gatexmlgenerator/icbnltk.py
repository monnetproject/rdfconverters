from nltk import tokenize
import itertools
import logging
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.stem.lancaster import LancasterStemmer
from nltk.corpus import stopwords
from rdflib import Graph
from rdfconverters.util import NS
from pkg_resources import resource_stream
from pprint import pprint as pp

logging.basicConfig(format='%(module)s %(levelname)s: %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

#-----------------------
# ICB

def parse_icb_graph():
    icb_path = resource_stream('rdfconverters.resources', 'mfo/ICBv1.1/icb.n3')
    icb = Graph()
    icb.parse(icb_path, format="n3")
    for n in NS:
        icb.bind(n, NS[n])
    return icb

def get_icb_labels(icb):
    labels = { s: o for s, o in icb.subject_objects(NS['rdfs']['label']) if o.language=="en"}
    for subj in labels.keys():
        labels[subj] = tokenize_words(str(labels[subj]))
    return labels

def get_icb_definitions(icb):
    definitions = { s: o for s, o in icb.subject_objects(NS['rdfs']['definition']) if o.language=="en"}

    for subj in definitions.keys():
        definition = str(definitions[subj])
        definitions[subj] = split_excluded(tokenize_words(definition))

    return definitions

def _get(lst, index, default=None):
    return lst[index] if len(lst) >= index +1 else default

def get_icb_label(icb, icb_uri):
    return str(_get([i for i in icb.objects(icb_uri, NS['rdfs']['label']) if i.language=="en"],0))

def get_icb_definition(icb, icb_uri):
    return str(_get([i for i in icb.objects(icb_uri, NS['rdfs']['definition']) if i.language=="en"],0))

#----------------
# Tokenising

def remove_business_gunk(phrase):
    gunk = ['wide range', 'company']
    for g in gunk:
        phrase = phrase.replace(g, '')
    return phrase

def split_excluded(words):
    if 'excludes' in words:
        included = words[:words.index('excludes')]
        excluded = words[words.index('excludes')+1:]
    else:
        included = words
        excluded = []

    return (included, excluded)

lmtzr = WordNetLemmatizer()
def lemmatize(word):
    return lmtzr.lemmatize(word)

stemmer = LancasterStemmer()
def stem(word):
    return stemmer.stem(word)


def tokenize_words(text):
    words = tokenize.word_tokenize(text.lower())
    # Remove stopwords and punctuation
    stop = stopwords.words("english") + list(";:'\".,&()")
    words = (w for w in words if w not in stop)
    # Get lemmas of words
    words = [stem(w) for w in words]
    return words

#---------------------
# Occurence counting

def contains_sublist(lst, sublst):
    n = len(sublst)
    return any((sublst == lst[i:i+n]) for i in range(len(lst)-n+1))

def is_excluded(definition, word_list):
    excluded = definition[1]
    return contains_sublist(excluded, word_list)

def count_total_occurences(lst, word_set):
    return sum(lst.count(word) for word in word_set)

def score(label, definition, word_set, exclude_labels=False):
    included = definition[0] if definition else []
    if exclude_labels:
        score = 0
    else:
        score = 2*count_total_occurences(list(set(label)), word_set)
    score += count_total_occurences(list(set(included)), word_set)
    return score

def max_items(items, key):
    m = max(items, key=key)


icb = parse_icb_graph()
labels = get_icb_labels(icb)
definitions = get_icb_definitions(icb)

def icb_matches(phrase, exclude_labels=False):
    '''
    phrase: String to perform matching on
    returns: tuple containing ICB code and english label
    '''

    phrase = remove_business_gunk(phrase)

    word_list = tokenize_words(phrase)
    word_set = set(word_list)
    print("Words:", word_set)

    scores = {}
    for icb_uri, label in labels.items():
        definition = definitions.get(icb_uri, None)

        if definition and is_excluded(definition, word_list):
            icb_score = -1
        else:
            icb_score = score(label, definition, word_set, exclude_labels=exclude_labels)

        scores[icb_uri] = icb_score

    max_score = max(v for k, v in scores.items())
    if max_score <= 0:
        return None

    max_values = [k for k, v in scores.items() if v == max_score]

    logger.debug ("---------------")
    logger.debug("Max score: %d" % max_score)
    for m in max_values:
        logger.debug(m)
        logger.debug (get_icb_label(icb, m))
        logger.debug (get_icb_definition(icb, m))
        logger.debug (labels.get(m))
        logger.debug (definitions.get(m))
        logger.debug ("---------------")

    matches = [(mv.rsplit('#',1)[1], get_icb_label(icb, mv)) for mv in max_values]
    return matches


