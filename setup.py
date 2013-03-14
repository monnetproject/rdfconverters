from setuptools import setup, find_packages
from os import walk
from os.path import join

def all_files(*paths):
    files = []
    for path in paths:
        files += [(w[0], [join(w[0],f) for f in w[2]]) for w in walk(path)]
    return files

setup(
    name = "rdfconverters",
    version = "0.1",
    packages = find_packages(),

    data_files = all_files('rdfconverters/resources'),

    install_requires = [
        'setuptools',
        'requests',
        'rdflib >= 3.2.3',
        'beautifulsoup4',
        'lxml',
        'distribute',
        'nltk >= 2.0.4'
    ],

    dependency_links = [
        'http://github.com/nltk/nltk/tarball/2and3#egg=nltk'
    ],

    entry_points = {
        'console_scripts': [
            'ie2rdf = rdfconverters.ie2rdf.ie2rdf:main',
            'merge_graphs = rdfconverters.merge_graphs:main',
            'daxquintuples2rdf = rdfconverters.daxquintuples2rdf.daxquintuples2rdf:main',
            'xbrl2rdf = rdfconverters.xbrl2rdf.xbrl2rdf:main',
            'en2rdf = rdfconverters.en2rdf.en2rdf:main',
            'gatexmlgenerator = rdfconverters.ie2rdf.gatexmlgenerator.gatexmlgenerator:main',
            'dax2rdf = rdfconverters.dax2rdf.dax2rdf:main',
        ]
    }
)
