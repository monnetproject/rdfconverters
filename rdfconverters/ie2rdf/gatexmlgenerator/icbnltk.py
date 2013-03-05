from nltk import tokenize
import itertools
import logging
from nltk.stem import PorterStemmer
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.stem.lancaster import LancasterStemmer
from nltk.corpus import stopwords
from rdflib import Graph, URIRef
from rdfconverters.util import NS
from pkg_resources import resource_stream
from pprint import pprint as pp
import re

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

def get_parents(icb, uri):
    parents = set()
    def __get_parents(node):
        parent = icb.value(subject=node, predicate=NS['rdfs']['subClassOf'])
        if parent is not None:
            parents.add(parent)
            __get_parents(parent)

    __get_parents(URIRef(uri))
    return parents


def remove_parents(icb, uris):
    orphans = set(uris)
    for uri in uris:
        if uri in orphans:
            orphans -= get_parents(icb, uri)
    return orphans

#----------------
# Tokenising

def remove_business_gunk(phrase):
    gunk = ['wide range', 'company', 'companies', 'industry', 'international',
        'services?', 'product(?!ion)s?', 'solutions', 'leading', 'sales', 'sector', 'integrated']
    for g in gunk:
        phrase = re.sub(g, '', phrase)
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

stemmer = PorterStemmer()
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

    logger.debug("*******%s" % phrase)

    phrase = remove_business_gunk(phrase)

    word_list = tokenize_words(phrase)
    word_set = set(word_list)
    print("Words: %s" % word_set)

    scores = {}
    for icb_uri, label in labels.items():
        definition = definitions.get(icb_uri, None)

        if definition and is_excluded(definition, word_list):
            icb_score = -1
        else:
            icb_score = score(label, definition, word_set, exclude_labels=exclude_labels)

        scores[icb_uri] = icb_score

    max_score = max(v for k, v in scores.items())
    logger.debug("Max score: %d" % max_score)
    if max_score <= 0:
        return None

    max_values = set(k for k, v in scores.items() if v == max_score)
    # e.g. if get 0500 and 0530 keep 0530 because it is more specific
    max_values = remove_parents(icb, max_values)
    logger.debug ("(%d) %s" % (len(max_values), [m[-4:] + " " + get_icb_label(icb, m) for m in max_values]))

    # Check if too many results to reasonably say we have an accurate match
    if len(max_values) > 2:
        return None

    #for m in max_values:
        #logger.debug ("%s - %s" % (get_icb_label(icb, m), get_icb_definition(icb, m)))

    matches = [(mv.rsplit('#',1)[1], get_icb_label(icb, mv)) for mv in max_values]
    return matches


