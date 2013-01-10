from setuptools import setup, find_packages
setup(
    name = "rdfconverters",
    version = "0.1",
    packages = find_packages(),

    install_requires = [
        'rdflib >= 3.2.3',
        'beautifulsoup4',
        'lxml',
        'distribute'
    ],

    entry_points = {
        'console_scripts': [
            'gate2rdf = rdfconverters.gate2rdf.gate2rdf:main',
            'merge_graphs = rdfconverters.merge_graphs:main',
            'daxquintuples2rdf = rdfconverters.daxquintuples2rdf.daxquintuples2rdf:main',
        ]
    }
)
