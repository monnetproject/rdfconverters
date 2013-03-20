import time
import os
import pickle
import sys
from bs4 import BeautifulSoup
import requests
from pprint import pprint as pp
import logging
import itertools
import argparse
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import XSD
from rdfconverters import util
from rdfconverters.cputil import CPNodeBuilder
from rdfconverters import cputil
from rdfconverters.util import NS
from pkg_resources import resource_stream
import re


logging.basicConfig(format='%(module)s %(levelname)s: %(message)s', level=logging.WARN)
logger = logging.getLogger(__name__)

if_path = resource_stream('rdfconverters.resources', 'mfo/IFv1.3/if.n3')
graph_if = Graph().parse(if_path, format='n3')

class Fetcher:
    BASE = "http://www.boerse-frankfurt.de"

    def fetch(self, url, params=None):
        logger.info("Fetching %s from web..." % url)
        rq = requests.get(url, params=params)
        return rq.text

    def fetch_constituents(self, isin):
        url = '%s/en/equities/indices/x+%s/constituents' % (self.BASE, isin)
        return self.fetch(url)

    def fetch_master_data(self, isin, lang):
        if lang=='de':
            url = '%s/%s/aktien/x+%s/stammdaten' % (self.BASE, lang, isin)
        else:
            url = '%s/%s/equities/x+%s/master+data' % (self.BASE, lang, isin)
        return self.fetch(url)

    def fetch_company_data(self, isin, lang):
        if lang == 'de':
            url = '%s/%s/aktien/x+%s/unternehmensdaten' % (self.BASE, lang, isin)
        else:
            url = '%s/%s/equities/x+%s/company+data' % (self.BASE, lang, isin)
        return self.fetch(url)

    def get_user_friendly_source_url(self, isin, lang):
        return "%s/%s/equities/x+%s" % (self.BASE, lang, isin)


class Scraper:
    """
    Fetch Deutsche Borse html data and convert into Python data structures
    """

    def __init__(self, fetcher):
        self.fetcher = Fetcher()

    def scrape(self, isin, timestamp):
        if timestamp is None:
            timestamp = int(time.time())*1000

        result = {'de': {}}

        # Source URLs
        result['de']['source'] = self.fetcher.get_user_friendly_source_url(isin, 'de')
        result['source'] = self.fetcher.get_user_friendly_source_url(isin, 'en')

        # Company data (only English necessary
        soup = BeautifulSoup(self.fetcher.fetch_company_data(isin, 'en'))
        result.update(self._scrape_company_data(soup))
        result.update(self._extract_basic_data(soup))
        result['timestamp'] = timestamp

        # Profiles
        profile_en = self._extract_profile(soup)
        if profile_en is not None:
            result['profile'] = profile_en
        soup = BeautifulSoup(self.fetcher.fetch_company_data(isin, 'de'))
        profile_de = self._extract_profile(soup)
        if profile_de is not None:
            result['de']['profile'] = profile_de

        result.update(self._scrape_master_data(isin, 'en'))
        result['de'].update(self._scrape_master_data(isin, 'de'))
        return result

    def _extract_basic_data(self, soup):
        # Basic data
        data = {}
        data['name'] = soup.select('.info h1')[0].text.strip()
        metadata = soup.select('.info h4')[0].text.strip().split()
        data['isin'] = metadata[2].rstrip(',')
        data['wkn'] = metadata[4].rstrip(',')
        if len(metadata) == 5:
            data['symbol'] = metadata[5].strip()
        return data

    def _scrape_master_data(self, isin, lang):
        html = self.fetcher.fetch_master_data(isin, lang)
        soup = BeautifulSoup(html)

        data = {}

        tables = soup.select('.contentarea table.single')
        # Master table
        master_table = self._table_to_2d_array(tables[0])
        for title, value in master_table[:-1]: # Leave out last item (sector/branche)
            value = value.strip()
            if title in ('Transparency Standard', 'Transparenzlevel'):
                data['transparencyStandard'] = value
            elif title in ('Market Segment', 'Marktsegment'):
                data['marketSegment'] = value
            elif title in ('Country', 'Land'):
                data['country'] = value
            elif title in ('Sector', 'Sektor'):
                data['sector'] = value
            elif title in ('Subsector', 'Subsektor'):
                data['subsector'] = value

        return data

    def _scrape_company_data(self, soup):
        data = {}

        contact_table = soup.select('.single.datenblatt.companyGrid')
        if not contact_table:
            return data

        contact = self._table_to_2d_array(contact_table[0])
        for title, value in contact:
            if title=='Address':
                data['street'], data['city'] = value.split('\n')[1:3]
            elif title=='Phone':
                data['phone'] = value
            elif title=='Fax':
                data['fax'] = value
            elif title=='URL':
                data['website'] = value
            elif title=='Email':
                data['email'] = value

            else:
                logger.warn("Unrecognised title (contact box): %s" % title)

        company_table = soup.select('.halfsingle.companyGrid')[0]
        company = self._table_to_2d_array(company_table)
        for title, value in company:
            if title=='Established':
                data['foundedIn'] = value
            elif title=='Transparancy Level':
                data['marketSegment'] = value
            elif title=='End of Business Year':
                eob = list(reversed(value.rstrip('/').split('/')))
                data['endOfBusinessYear'] = '-'.join(eob)
            elif title=='Accounting Standard':
                data['accountingStandard'] = value
            elif title=='Total Capital Stock':
                data['totalCapitalStock'] = value
            elif title=='Admission Date':
                adm = value.rstrip('/').split('/')
                data['admissionDate'] = "%s-%s-%s" % (adm[2], adm[1], adm[0])
            else:
                logger.warn("Unrecognised title (company box): %s" % title)
        return data

    def _extract_profile(self, soup):
        profile = soup.find('div', {'style': 'font-size:11px'})
        if profile:
            # Get raw html of children
            return ''.join(str(c) for c in profile.contents)
        return None

    def _get_tag_text(self, tag):
        return '\n'.join(a.strip() for a in tag.strings)

    def _table_to_2d_array(self, table):
        data=[]
        for tr in table.find_all('tr'):
            row=[self._get_tag_text(tag) for tag in itertools.chain(tr.find_all('th'), tr.find_all('td'))]
            data.append(row)
        return data

class Searcher:
    def search_index_constituents(self, isin):
        url = 'http://www.boerse-frankfurt.de/en/equities/indices/x+%s/constituents' % isin
        html = requests.get(url).text
        soup = BeautifulSoup(html)
        results = soup.find_all('td', {'class': 'column-name'})

        name_isins = []
        for result in results:
            isin = result.contents[-1].strip()
            name = result.find('a').text.strip()
            name_isins.append((isin, name))

        return sorted(name_isins, key=lambda k: k[0])


class RDFConverter:
    '''
    Converts output from Scraper to RDF.
    '''
    def __init__(self):
        pass

    def to_rdf(self, data):
        a = NS['rdf']['type']
        g = Graph()
        for ns in NS:
            g.bind(ns, NS[ns])

        id_ = "%s__%s" % (data['isin'], data['timestamp'])
        id_node = NS['cp'][id_]

        g.add((id_node, a, NS['cp']['CompanyProfile']))
        g.add((id_node, NS['cp']['stockExchange'], NS['if']['deutsche_borse_singleton']))

        dt = util.timestamp_to_datetime(data['timestamp'])
        g.add((id_node, NS['cp']['instant'], Literal(dt, datatype=XSD.dateTime)))

        if 'admissionDate' in data:
            g.add((id_node, NS['dax']['admissionDate'], Literal(data['admissionDate'], datatype=XSD.date)))

        # Add companyId, falling back to ISIN if unavailable
        companyid = cputil.companyid(data['isin'])
        if companyid is None:
            companyid = data['isin']
        g.add((id_node, NS['cp']['companyId'], Literal(companyid)))

        standard = {
            'cp': ('email', 'fax', 'phone', 'isin', 'symbol', 'website', 'street', 'city'),
            'dax': ('endofBusinessYear', 'foundedIn', 'wkn')
        }
        for ns, keys in standard.items():
            for key in keys:
                if key in data:
                    g.add((id_node, NS[ns][key], Literal(data[key]) ))

        if 'country' in data:
            country = cputil.country_from_name(data['country'])
            g.add((id_node, NS['cp']['country'], country))

        for key in ('profile', 'source'):
            if key in data:
                g.add((id_node, NS['cp'][key], Literal(data[key], lang='en')))
            if key in data['de']:
                g.add((id_node, NS['cp'][key], Literal(data['de'][key], lang='de')))

        for key in 'marketSegment', 'transparencyStandard', 'accountingStandard':
            if key in data:
                segment = re.sub(r'[\(\)#]', '', data[key]).lower().replace('german gaap', '').replace(' ', '_').strip('_') + '_singleton'
                g.add((id_node, NS['dax'][key], NS['dax'][segment] ))

        key = 'totalCapitalStock'
        if key in data:
            if '\u20ac' not in data[key]:
                print("WARNING: Ignoring total capital stock. No euro sign in: %s" % data[key])
            else:
                monetary = re.sub('[^0-9.]', '', data[key]) + "EUR"
                g.add((id_node, NS['dax'][key], Literal(monetary, lang='en')))

        key = 'endOfBusinessYear'
        if key in data:
           g.add((id_node, NS['dax'][key], Literal(data[key], lang='en')))

        if 'subsector' in data:
            daxname = data['subsector'].replace(' ', '').replace('+', 'And').replace('-','')
            node = NS['dax'][daxname]

            # Map the DAX sector to ICB
            for icb in graph_if.objects(node, NS['owl']['equivalentClass']):
                CPNodeBuilder(g, id_node).structured().sector_value('sector', icb)
                break
            else:
                logger.warn("No ICB mapping found for %s" % node)

        # Name
        if 'name' in data:
            CPNodeBuilder(g, id_node).structured().string_value('companyName', data['name'])

        return g



def search_index_constituents(isin, output_file=None):
    searcher = Searcher()
    results = searcher.search_index_constituents(isin)

    if output_file:
        logger.info("Writing results to %s" % output_file)
        with open(output_file, 'w+') as f:
            for result in results:
                f.write(' '.join(result) + '\n')

    for result in results:
        print (' '.join(result))

def scrape(isin, outputfile, pickled=False, timestamp=None):
    fetcher = Fetcher()
    scraper = Scraper(fetcher)
    scraped = scraper.scrape(isin, timestamp=timestamp)
    #pp(scraped)

    if pickled:
        with open(outputfile, 'wb') as f:
            sys.setrecursionlimit(2000)
            pickle.dump(scraped, f, pickle.DEFAULT_PROTOCOL)
    else:
        rdfconvert(scraped, outputfile)

def rdfconvert(scraped, outputfile):
    r = RDFConverter()
    graph = r.to_rdf(scraped)
    if outputfile:
        with open(outputfile, 'wb+') as f:
            f.write(graph.serialize(format='n3'))
    return graph


def main():
    parser = argparse.ArgumentParser(
        description='Searcher, scraper and RDF converter for EuroNext.'
    )

    subparser = parser.add_subparsers(help='commands', dest='command')

    # Search command
    search_command = subparser.add_parser('search', help='Search Deutsche Borse index constituents')
    search_command.add_argument('isin', help='ISIN of the Deutsche Borse index')
    search_command.add_argument('-o', dest='output_file', help='Output file for results')

    def add_pickle_argument(command):
        command.add_argument('--pickle',action='store_true', default=False,
            help='Output as pickled objects. Can be converted to RDF using the " + \
           "rdfconvert command. Used to allow changes to the RDF format without having to write converters for RDF output files')

    # Scrape commands
    scrapeone_command = subparser.add_parser('scrapeone', help='Scrape a page given ISIN')
    scrapeone_command.add_argument('isin', help='ISIN number of company')
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

    args = parser.parse_args()

    if args.command == 'search':
        search_index_constituents(args.isin, output_file=args.output_file)
    elif args.command == 'scrapeone':
        scrape(args.isin, args.outputfile, args.pickle)
    elif args.command == 'scrape':
        extension = 'pickle' if args.pickle else 'n3'
        with open(args.inputfile) as f:
            isins = [l[0] for l in util.read_space_delimited_file(f)]
            print(len(isins), " ISINs found")
        for i, isin in enumerate(isins):
            timestamp = int(time.time() * 1000)
            outputfile = "%s/%s-%s.%s" % (args.outputdir, isin, timestamp, extension)
            print("%d. Scraping %s to %s" % (i+1, isin, outputfile))
            try:
                scrape(isin, outputfile, args.pickle, timestamp=timestamp)
            except Exception as e:
                logger.exception("Failed to scrape %s: %s", isin, str(e))
            time.sleep(1)
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


if __name__=='__main__':
    main()
