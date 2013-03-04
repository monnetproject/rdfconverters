import os
import pickle
import sys
from bs4 import BeautifulSoup
import requests
from pprint import pprint
import logging
import itertools
import re
import time
import json
import argparse
from datetime import datetime
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import XSD
from rdfconverters import util
from rdfconverters.cputil import CPNodeBuilder
from rdfconverters.util import NS
from pkg_resources import resource_string

logging.basicConfig(format='%(module)s %(levelname)s: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

f = resource_string('rdfconverters.resources', 'isin_companyid_map.txt').decode('utf-8')
isin_companyid_map = {}
for entry in f.split('\n'):
    if len(entry.strip()) > 0:
        isin, companyid = entry.split(' ')
        isin_companyid_map[isin] = companyid

class Fetcher:
    """
    Responsible for fetching EuroNext HTML data.
    """

    BASE = "https://europeanequities.nyx.com"

    def fetch(self, url, params=None):
        logger.info("Fetching %s from web..." % url)
        rq = requests.get(url, params=params)
        return rq.text

    def get_user_friendly_source_url(self, isin, mic, lang):
        return "%s/%s/products/equities/%s-%s" % (self.BASE, lang, isin, mic)

    def fetch_company_profile(self, isin, mic, lang):
        url = "%s/%s/nyx-company-profile/ajax?instrument_id=%s-%s" % (self.BASE, lang, isin, mic)
        return self.fetch(url)

    def fetch_factsheet(self, isin, mic, lang):
        url = "%s/%s/factsheet-ajax?instrument_id=%s-%s&instrument_type=equities" % (self.BASE, lang, isin, mic)
        return self.fetch(url)

    def fetch_quote(self, isin, mic, lang):
        url = "%s/%s/nyx_eu_listings/real-time/quote?isin=%s&mic=%s" % (self.BASE, lang, isin, mic)
        return self.fetch(url)

class Scraper:
    """
    Fetch EuroNext html data and convert into Python data structures
    e.g.
    > fetcher = Fetcher()
    > scraper = Scraper(fetcher)
    > scraper.scrape("BE0003764785", "XBRU", "en")
      { ....... }
    """

    def __init__(self, fetcher):
        self.fetcher = fetcher

    def scrape(self, isin, mic, langs=["en", "pt-pt", "nl", "fr"], timestamp=int(time.time())*1000):
        if isinstance(langs, str):
            langs = [langs]
        result = {}
        result.update( {'sources': {lang:self.fetcher.get_user_friendly_source_url(isin, mic, lang) for lang in langs} } )

        result['profile'] = {}
        for lang in langs:
            result['profile'][lang] = self._scrape_company_profile(isin, mic, lang)
        result['factsheet'] = self._scrape_factsheet(isin, mic, "en")
        result['quote'] = self._scrape_quote(isin, mic, "en")
        result['timestamp'] = timestamp
        result.update( {'isin': isin, 'mic': mic} )
        return result

    def _scrape_company_profile(self, isin, mic, lang):
        data = {}

        html = self.fetcher.fetch_company_profile(isin, mic, lang)
        if not html:
            return data
        soup = BeautifulSoup(html)

        # Profile
        profile = ''.join([str(a) for a in soup.find('div', {'class': 'detail'})]).strip()
        data['profile'] = profile

        for table in soup.find_all('table'):
            t = self._table_to_2d_array(table)
            if table['id'] and len(t)>1:

                # Key Executives
                if table['id'] == "top-management-table-values":
                    data['management']=[{'function': row[0], 'name': row[1]} for row in t[1:]]
                # Financial figures
                elif table['id'].startswith('key-figures-table'):
                    years = t[0][1:]
                    concepts = [row[0] for row in t[1:]]
                    figures = {}
                    for i in range(len(concepts)):
                        figures[concepts[i]] = {}
                        for j in range(len(years)):
                            figures[concepts[i]][years[j]] = t[i+1][j+1]
                    data['figures'] = figures
                # Shareholders
                elif table['id'] == 'shareholder-info-table-values':
                    data['shareholders']=[{'name': row[0], 'value': row[1].rstrip('%').replace(',','.')} for row in t[1:]]

        # Address
        address={}
        groups = soup.find('div', {'id':'company-profile-address'}).findAll('div', {'class':'address-group'})

        if groups:
            txt = [n.strip() for n in groups.pop(0).findAll(text=True) if len(n.strip())]
            if txt:
                address['companyName'] = txt.pop(0)
            if txt:
                address['country'] = txt.pop()
            if txt:
                address['city'] = txt.pop()
            if txt:
                address['street'] = '\n'.join(txt)
        for group in groups:
            txt = group.find(text=True).strip()
            if txt.startswith("http"):
                address['website'] = txt
            elif ':' in txt:
                split = txt.split(':')
                field, value = split[0].strip(), ''.join(split[1:]).strip()
                if field == "Phone number":
                    address['phone'] = value
                elif field == "Fax":
                    address['fax'] = value
        data['address'] = address

        # Investor contact
        invest_contact = soup.find('div', {'id': 'company-profile-investor-contact'}).find_all('div', {'class': 'address-group'})
        data['investor_contact'] = {}
        for f,v in zip(['name', 'email', 'phone'], invest_contact):
            if len(v.contents) == 2:
                data['investor_contact'][f] = str(v.contents[0]).strip()

        return data

    def _scrape_factsheet(self, isin, mic, lang):
        html = self.fetcher.fetch_factsheet(isin, mic, lang)
        soup = BeautifulSoup(html)
        factsheet = {}

        # CFI
        left = soup.select('.column.left > div')
        if left and len(left)==3:
            factsheet['cfi'] = left[1].div.string.split(': ')[-1]

        # ICB
        right = soup.select('.if-block.icb strong')
        if right:
            factsheet['icb'] = right[-1].string.strip().split(', ')

        return factsheet

    def _scrape_quote(self, isin, mic, lang):
        html = self.fetcher.fetch_quote(isin, mic, lang)
        soup = BeautifulSoup(html)

        quote = {}
        quote['symbol'] = soup.find('div', {'class': 'sub-container'}).find('div', {'class': 'first-column box-column'}).span.string
        quote['name'] = soup.find('span', {'class': 'instrument-name'}).string

        return quote

    def _table_to_2d_array(self, table):
        data=[]
        for tr in table.find_all('tr'):
            row=[cell.text.strip() for cell in itertools.chain(tr.find_all('th'), tr.find_all('td'))]
            data.append(row)
        return data

class Searcher:
    """
    Search for companies by keyword or ICB
    """

    @staticmethod
    def print_search_results(results):
        if not results:
            print("No results found")
            return

        col=(13, 5, 30)
        print("%*s%*s%*s" % (col[0],'ISIN',col[1],'MIC',col[2],'NAME'))
        print('-'*(sum(col)))
        for r in results:
            print('%*s%*s%*s' % (col[0],r['isin'],col[1],r['mic'],col[2],r['name']))

    def search(self, keyword='', icb=None, maxresults=None):
        # Get the CSRF token
        url = "https://europeanequities.nyx.com/en/markets/nyse-euronext/product-directory"
        html = requests.get(url).text
        soup = BeautifulSoup(html)
        csrf = soup.find('form', {'id': 'filters_block_form'}).find('input', {'name': 'form_build_id'})['value']


        # Execute search
        params = {
            'nameIsinSym': keyword,
            'form_build_id': csrf,
            'op': 'Apply',
            'initialLetter': '',
            'form_id': 'nyx_pd_stocks_filter',
        }
        if icb:
            params['industry[%s]'%icb] = icb
            for i in range(1, len(icb)):
                icbround = icb[:-i] + '0'*i
                params['industry[%s]'%icbround] = icbround
        results = requests.post(url, params).text

        # Get the form key that was passed to the javascript
        key = re.search("formKey=(nyx_pd_filter_values:.*?)\"", results).group(1)
        logger.debug("Found key: %s", key)

        # Make the AJAX request to get the JSON results
        url="https://europeanequities.nyx.com/pd/stocks/data?formKey="+key

        total = 1
        offset = 0
        results_per_page = 20 # Seems to be the maximum supported
        searchData = []
        while offset < total:
            jsonresponse = requests.post(url, {'sEcho': 1, 'iDisplayStart': offset, 'iDisplayLength': results_per_page})
            jsonobj = json.loads(jsonresponse.text)
            pprint(jsonobj)

            total = jsonobj['iTotalDisplayRecords']

            num_results = len(jsonobj['aaData'])
            if maxresults is not None and offset + num_results >= maxresults:
                searchData += jsonobj['aaData'][:maxresults-offset]
                break
            else:
                offset += num_results
                searchData += jsonobj['aaData']

	# Create list of results containing company name, isin and mic
        companies=[]
        for company in searchData:
            if isinstance(company, (list, tuple)):
                result = dict(
                    name = re.search("_blank\">\s*(.*?)\s*</a>", company[0]).group(1),
                    isin = company[1],
                    mic = re.search(r'/[A-Z0-9]{12}-([A-Z]{4})"', company[0]).group(1)
                )
                companies.append(result)
        return companies

class RDFConverter:
    '''
    Converts output from Scraper to RDF.
    '''

    def __init__(self, scraped):
        self.scraped = scraped
        id = "%s_%s_%s" % (self.scraped['isin'], self.scraped['mic'], self.scraped['timestamp'])
        self.id_node = NS['cp'][id]

        self.g = Graph()
        for ns in NS:
            self.g.bind(ns, NS[ns])

        self.en2xml_langs = {'en': 'en', 'pt-pt': 'pt', 'nl': 'nl', 'fr': 'fr'}

    def _write_quote(self):
        quote = self.scraped['quote']
        # Ticker symbol
        if 'symbol' in quote:
            self.g.add((self.id_node, NS['cp']['symbol'], Literal(quote['symbol'])))

        # Company name
        if 'name' in quote:
            company_name = quote['name']
            CPNodeBuilder(self.g, self.id_node).structured().string_value('companyName', company_name)

    def _write_profile(self):
        for lang, profile in self.scraped['profile'].items():
            if not profile:
                continue
            lang = self.en2xml_langs[lang]

            # Unstructured text
            if 'profile' in profile:
                self.g.add((self.id_node, NS['cp']['profile'], Literal(profile['profile'], lang=lang)))

            # Address
            if 'street' in profile['address']:
                self.g.add((self.id_node, NS['cp']['street'], Literal(profile['address']['street'])))
            if 'city' in profile['address']:
                self.g.add((self.id_node, NS['cp']['city'], Literal(profile['address']['city'], lang=lang)))
            if 'country' in profile['address']:
                self.g.add((self.id_node, NS['cp']['country'], Literal(profile['address']['country'], lang=lang)))

            # Management
            for manager in profile.get('management', []):
                node = NS['en']["%s_%d" % (manager['name'].replace(' ', '_'), self.scraped['timestamp'])]

                fln = manager['name'].index(' ')
                if fln:
                    first, last = manager['name'][:fln], manager['name'][fln+1:]
                else:
                    first, last = None, None

                self.g.add((self.id_node, NS['en']['topManagement'], node))
                self.g.add((node, NS['rdf']['type'], NS['en']['person']))
                self.g.add((node, NS['en']['name'], Literal(manager['name'])))
                self.g.add((node, NS['en']['function'], Literal(manager['function'], lang=lang)))
                if first:
                    self.g.add((node, NS['en']['firstName'], Literal(first)))
                if last:
                    self.g.add((node, NS['en']['lastName'], Literal(last)))

            # Shareholders - only English as nothing useful is translated
            if lang=='en':
                for shareholder in self.scraped['profile'][lang]['shareholders']:
                    node = NS[lang]["%s_%d" % (shareholder['name'].replace(' ', '_'), self.scraped['timestamp'])]
                    self.g.add((self.id_node, NS[lang]['shareholderValue'], node))
                    self.g.add((node, NS[lang]['name'], Literal(shareholder['name'])))
                    self.g.add((node, NS[lang]['value'], Literal(shareholder['value'], datatype=XSD.float)))

    def _write_factsheet(self):
        factsheet = self.scraped['factsheet']
        # CFI
        if 'cfi' in factsheet:
            cfi_singleton = NS['cfi'][factsheet['cfi'].lower() + "_singleton"]
            self.g.add((self.id_node, NS['en']['cfi'], cfi_singleton))
            fields = ('category', 'group', 'first', 'second', 'third', 'fourth')
            for value, field in zip(factsheet['cfi'], fields):
                self.g.add((cfi_singleton, NS['cfi'][field], Literal(value)))

        # ICB
        if 'icb' in factsheet:
            sector_value = NS['icb']['ICB'+factsheet['icb'][0]]
            CPNodeBuilder(self.g, self.id_node).structured().sector_value('sector', sector_value)

    def to_rdf(self):
        a = NS['rdf']['type']

        self.g.add((self.id_node, a, NS['cp']['CompanyProfile']))
        self.g.add((self.id_node, NS['cp']['stockExchange'], NS['if']['euronext_singleton']))
        # Use both cp:stockExchange and if:origin while transitioning to cp: ontology
        self.g.add((self.id_node, NS['if']['origin'], NS['if']['euronext_singleton']))
        self.g.add((self.id_node, NS['cp']['isin'], Literal(self.scraped['isin'])))

        # Add companyId if available
        if self.scraped['isin'] in isin_companyid_map.keys():
            self.g.add((self.id_node, NS['cp']['companyId'], Literal(isin_companyid_map[self.scraped['isin']])))

        dt = util.timestamp_to_datetime(self.scraped['timestamp'])
        self.g.add((self.id_node, NS['cp']['instant'], Literal(dt, datatype=XSD.dateTime)))

        for lang, source in self.scraped['sources'].items():
            self.g.add((self.id_node, NS['cp']['source'], Literal(source, lang=self.en2xml_langs[lang])))

        self._write_quote()
        self._write_profile()
        self._write_factsheet()
        return self.g

def search(keyword=None, icb=None, outputfile=None, maxresults=None):
    searcher = Searcher()
    if icb:
        print("Searching by ICB code %s" % icb)
        results = searcher.search(icb=icb, maxresults=maxresults)
    elif keyword:
        print("Searching by keyword %s" % keyword)
        results = searcher.search(keyword, maxresults=maxresults)

    Searcher.print_search_results(results)

    if outputfile:
        with open(outputfile, "w") as f:
            print("Writing ISIN and MICs to %s" % outputfile)
            for r in results:
                f.write('%s %s\n' % (r['isin'], r['mic']))

def scrape(isin, mic, outputfile, pickled=False, timestamp=None):
    fetcher = Fetcher()
    scraper = Scraper(fetcher)
    if timestamp:
        scraped = scraper.scrape(isin, mic, timestamp=timestamp)
    else:
        scraped = scraper.scrape(isin, mic)

    if pickled:
        with open(outputfile, 'wb') as f:
            sys.setrecursionlimit(2000)
            pickle.dump(scraped, f, pickle.DEFAULT_PROTOCOL)
    else:
        rdfconvert(scraped, outputfile)

def rdfconvert(scraped, outputfile):
    r = RDFConverter(scraped)
    graph = r.to_rdf()
    if outputfile:
        with open(outputfile, 'wb') as f:
            f.write(graph.serialize(format='n3'))
    return graph


def main():
    parser = argparse.ArgumentParser(
        description='Searcher, scraper and RDF converter for EuroNext.'
    )

    subparser = parser.add_subparsers(help='commands', dest='command')

    # Search command
    search_command = subparser.add_parser('search', help='Search EuroNext website')
    search_subcommands = search_command.add_subparsers(help='Search commands', dest='search_subcommand')
    search_command.add_argument('-o', dest='output', help='Write search results to file, which can be used as input to the scrape command')
    search_command.add_argument('--max-results', default=None, type=int, dest='maxresults', help='Maximum results from search')

    keyword_command = search_subcommands.add_parser('keyword', help='Search EuroNext website by keyword')
    keyword_command.add_argument('keyword', help='Keyword to search by')
    icb_command = search_subcommands.add_parser('icb', help='Search EuroNext website by ICB code')
    icb_command.add_argument('icb', help='ICB code to search by (e.g. 7000 will find all matching 7XXX)')

    def add_pickle_argument(command):
        command.add_argument('--pickle',action='store_true', default=False,
            help='Output as pickled objects. Can be converted to RDF using the " + \
           "rdfconvert command. Used to allow changes to the RDF format without having to write converters for RDF output files')
    def add_extract_profiles_argument(command):
        command.add_argument('--extract-profiles', dest='extract_profiles',
            help='Extract cp:profile as text files into the given folder, which can then be processed with GATE.')

    # Scrape commands
    scrapeone_command = subparser.add_parser('scrapeone', help='Scrape a page from EuroNext given ISIN and MIC')
    scrapeone_command.add_argument('isin', help='ISIN number of company')
    scrapeone_command.add_argument('mic', help='ISO-10383 MIC for company (in URL of source URL)')
    scrapeone_command.add_argument('outputfile', help='Path to a writable output file')
    add_pickle_argument(scrapeone_command)

    scrape_command = subparser.add_parser('scrape', help='Scrape from a file')
    scrape_command.add_argument('inputfile', help='Path to file containing space-separated ISINs and MICs, one per line.' + \
      " Can be generated with the 'search' command.")
    scrape_command.add_argument('outputdir', help='Path to a writeable output directory')
    add_pickle_argument(scrape_command)

    # rdfconvert command
    rdfconvert_command = subparser.add_parser('rdfconvert', help='Convert pickled objects to RDF')
    rdfconvert_command.add_argument('inputpath', help='Source file or folder (if --batch)')
    rdfconvert_command.add_argument('outputpath', help='Destination file or folder (if --batch)')
    rdfconvert_command.add_argument('--batch', action='store_true', default=False, help='Convert all .pickle files recursively in "inputpath"')

    extract_profiles_command = subparser.add_parser('extractprofiles',
      help='Extract cp:profile as text files into the given folder, which can then be processed with GATE')
    extract_profiles_command.add_argument('inputdir', help='Directory containing cp:graphs')
    extract_profiles_command.add_argument('outputdir', help='Output directory')

    args = parser.parse_args()

    if args.command == 'search':
        if hasattr(args, 'keyword'):
            search(keyword=args.keyword, outputfile=args.output, maxresults=args.maxresults)
        elif hasattr(args, 'icb'):
            search(icb=args.icb, outputfile=args.output, maxresults=args.maxresults)
    elif args.command == 'scrapeone':
        scrape(args.isin, args.mic, args.outputfile, args.pickle)
    elif args.command == 'scrape':
        with open(args.inputfile) as f:
            isins_mics = util.read_space_delimited_file(f)
        for isin_mic in isins_mics:
            extension = 'pickle' if args.pickle else 'n3'
            timestamp = int(time.time() * 1000)
            outputfile = "%s/%s-%s-%s.%s" % (args.outputdir, isin_mic[0], isin_mic[1], timestamp, extension)
            print("Scraping %s, %s to %s" % (isin_mic[0], isin_mic[1], outputfile))
            try:
                scrape(isin_mic[0], isin_mic[1], outputfile, args.pickle, timestamp=timestamp)
            except Exception as e:
                logger.exception("Failed to scrape %s" % isin_mic)
    elif args.command == 'rdfconvert':
        if args.batch:
            files = list(util.traverse_mirror(args.inputpath, args.outputpath, '.pickle', '.n3'))
        else:
            files = [(args.inputpath, args.outputpath)]

        for inputfile, outputfile in files:
            print("Converting %s to %s" % (inputfile, outputfile))
            with open(inputfile, 'rb') as f:
                scraped = pickle.load(f)
                rdfconvert(scraped, outputfile)
    elif args.command == 'extractprofiles':
        for directory, file in util.traverse(args.inputdir, '.n3'):
            # Output into language-specific folder
            inputfile = directory + os.sep + file
            g = Graph()
            g.parse(inputfile, format='n3')
            for cp_id, _, profile in g.triples((None, NS['cp']['profile'], None)):
                outdir = args.outputdir + os.sep + profile.language
                if not os.path.exists(outdir):
                    os.makedirs(outdir)

                id = cp_id.split('#')[1]
                outputfile = "%s/%s.txt" % (outdir, id)
                print(inputfile, "->", outputfile)
                with open(outputfile, "w+") as f:
                    f.write(profile)


if __name__=='__main__':
    main()

