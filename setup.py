from setuptools import setup, find_packages
setup(
    name = "rdfconverters",
    version = "0.1",
    packages = find_packages(),

    include_package_data = True,
    package_data = {
        'rdfconverters.xbrl2rdf': ['schemas/*.n3'],
        'rdfconverters.ie2rdf.gatexmlgenerator': ['*.txt', 'GATEAnnotator'],
    },

    install_requires = [
        'setuptools',
        'requests',
        'rdflib >= 3.2.3',
        'beautifulsoup4',
        'lxml',
        'distribute'
    ],

    entry_points = {
        'console_scripts': [
            'ie2rdf = rdfconverters.ie2rdf.ie2rdf:main',
            'gatexmlgenerator = rdfconverters.ie2rdf.gatexmlgenerator.gatexmlgenerator:main',
            'merge_graphs = rdfconverters.merge_graphs:main',
            'daxquintuples2rdf = rdfconverters.daxquintuples2rdf.daxquintuples2rdf:main',
            'xbrl2rdf = rdfconverters.xbrl2rdf.xbrl2rdf:main',
            'en2rdf = rdfconverters.en2rdf.en2rdf:main',
        ]
    }
)
