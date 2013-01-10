from bs4 import BeautifulSoup
import requests
from pprint import pprint
import logging
import itertools
import re
import time
import json
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import XSD
from util import NS

logging.basicConfig(format='%(module)s %(levelname)s: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class Fetcher:
    """
    Responsible for fetching EuroNext HTML data.
    """

    # Caching is just for development, to avoid scraping the site while testing code
    CACHED_ISIN="BE0003764785"
    CACHED_MIC="XBRU"
    CACHED_LANG="en"
    CACHES = {
        'https://europeanequities.nyx.com/%s/nyx-company-profile/ajax?instrument_id=%s-%s' % (CACHED_LANG, CACHED_ISIN, CACHED_MIC): 'cached_table.html',
        'https://europeanequities.nyx.com/%s/factsheet-ajax?instrument_id=%s-%s&instrument_type=equities' % (CACHED_LANG, CACHED_ISIN, CACHED_MIC): 'cached_factsheet.html',
        'https://europeanequities.nyx.com/%s/nyx_eu_listings/real-time/quote?isin=%s&mic=%s' % (CACHED_LANG, CACHED_ISIN, CACHED_MIC): 'cached_quote.html',
        'https://europeanequities.nyx.com/%s/markets/nyse-euronext/brussels/product-directory' % (CACHED_LANG): 'cached_search.html'
    }
    
    BASE = "https://europeanequities.nyx.com"

    def __init__(self, use_cache=False):
        self.use_cache = use_cache

    def fetch(self, url, params=None):
        in_cache=self.use_cache and url in self.CACHES
        if in_cache and params is None:
            try:
                with open(self.CACHES[url], "r") as f:
                    logger.info("Fetching %s from cache %s..." % (url, self.CACHES[url]))
                    return f.read()
            except IOError:
                in_cache=False

        if not in_cache or params:
            logger.info("Fetching %s from web..." % url)
            rq = requests.get(url, params=params)
            if url in self.CACHES:
                with open(self.CACHES[url], "w") as f:
                    f.write(rq.text)
            return rq.text

    def get_source_url(self, isin, mic, lang):
        '''Returns the URL of the HTML page where the data can be viewed by a human'''
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

class Parser:
    """
    Convert EuroNext html data into Python data structures
    e.g.
    > fetcher = Fetcher(use_cache=False)
    > parser = Parser(fetcher)
    > parser.parse("BE0003764785", "XBRU", "en")
      { ....... }
    """

    def __init__(self, fetcher):
        self.fetcher = fetcher

    def parse(self, isin, mic, lang):
        lang = lang.lower()
        result = {}
        result.update( {'source': self.fetcher.get_source_url(isin, mic, lang) } )
        result.update( self._parse_company_profile(isin, mic, lang) )
        result.update( self._parse_factsheet(isin, mic, lang) )
        result.update( self._parse_quote(isin, mic, lang) )
        result.update( {'isin': isin, 'mic': mic, 'lang': lang} )
        return result

    def _parse_company_profile(self, isin, mic, lang):
        html = self.fetcher.fetch_company_profile(isin, mic, lang)
        soup = BeautifulSoup(html)

        data = {}

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

    def _parse_factsheet(self, isin, mac, lang):
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

    def _parse_quote(self, isin, mic, lang):
        html = self.fetcher.fetch_quote(isin, mic, lang)
        soup = BeautifulSoup(html)

        quote = {}
        quote['symbol'] = soup.find('div', {'class': 'sub-container'}).find('div', {'class': 'first-column box-column'}).span.string

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

    def search(self, keyword='', icb=None):
        # Get the CSRF token
        url = "https://europeanequities.nyx.com/en/markets/nyse-euronext/brussels/product-directory"
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
        jsonresponse = requests.post(url, {'iDisplayLength': 100})
        jsonobj = json.loads(jsonresponse.text)

	# Create list of results containing company name, isin and mic
        companies=[]
        for company in jsonobj['aaData']:
            if isinstance(company, (list, tuple)):
                result = dict(
                    name = re.search("_blank\">\s*(.*?)\s*</a>", company[0]).group(1),
                    isin = company[1],
                    mic = company[2]
                )
                companies.append(result)
        return companies

class RDFConverter:
    def __init__(self):
        pass

    def parsed_to_rdf(self, parsed, timestamp=int(time.time()*1000)):
        ''' Convert the output of the parser into an RDF graph '''

        g = Graph()
        for ns in NS:
            g.bind(ns, NS[ns])

        id = "%s_%s" % (parsed['isin'], timestamp)
        id_node = NS['en'][id]
        a = NS['rdf']['type']
        
        g.add((id_node, a, NS['en']['Company']))
        g.add((id_node, NS['cp']['StockExchange'], NS['if']['euronext_singleton']))

        g.add((id_node, NS['cp']['source'], Literal(parsed['source'], lang=parsed['lang'])))
        g.add((id_node, NS['cp']['isin'], Literal(parsed['isin'])))
    
        if 'symbol' in parsed:
            g.add((id_node, NS['cp']['symbol'], Literal(parsed['symbol'])))
        if 'profile' in parsed:
            g.add((id_node, NS['cp']['profile'], Literal(parsed['profile'], lang=parsed['lang'])))

        # Address
        for addr in parsed['address']:
            lang = parsed['lang'] if addr in ['city', 'country'] else None
            g.add((id_node, NS['cp'][addr], Literal(parsed['address'][addr], lang=lang)))

        # Management
        for manager in parsed['management']:
            node = NS['en']["%s_%d" % (manager['name'].replace(' ', '_'), timestamp)]

            fln = manager['name'].index(' ')
            if fln:
                first, last = manager['name'][:fln], manager['name'][fln+1:]
            else:
                first, last = None, None

            g.add((id_node, NS['en']['topManagement'], node))
            g.add((node, a, NS['en']['person']))
            g.add((node, NS['en']['name'], Literal(manager['name'])))
            g.add((node, NS['en']['function'], Literal(manager['function'], lang=parsed['lang'])))
            if first:
                g.add((node, NS['en']['firstName'], Literal(first)))
            if last:
                g.add((node, NS['en']['lastName'], Literal(last)))

        # Shareholders
        for shareholder in parsed['shareholders']:
            node = NS['en']["%s_%d" % (shareholder['name'].replace(' ', '_'), timestamp)] 
            g.add((id_node, NS['en']['shareholderValue'], node))
            g.add((node, NS['en']['name'], Literal(shareholder['name'])))
            g.add((node, NS['en']['value'], Literal(shareholder['value'], datatype=XSD.float)))

        # CFI
        if 'cfi' in parsed:
            cfi_singleton = NS['cfi'][parsed['cfi'][:2].lower() + "_singleton"]
            fields = ('category', 'group', 'first', 'second', 'third', 'fourth')
            for value, field in zip(parsed['cfi'], fields):
                g.add((cfi_singleton, NS['cfi'][field], Literal(value)))

        # ICB
        if 'icb' in parsed:
            g.add((id_node, a, NS['icb']['ICB'+parsed['icb'][0]]))

        return g
        


isin, mic = "BE0003764785", "XBRU"
lang = "en"
langs = ["en", "fr", "pt", "nl"]

fetcher = Fetcher(use_cache=True)
parser = Parser(fetcher)

# Example of scraping and converting to RDF
parsed = parser.parse(isin, mic, lang)
#pprint(parsed)

r = RDFConverter()
graph = r.parsed_to_rdf(parsed)
print (graph.serialize(format='n3').decode('utf-8'))


'''
# Example of searching
searcher = Searcher()
# By keyword
results = searcher.search("4ENERGY")
logger.info("Search results by keyword:")
pp(results)
# By ICB sector code
results = searcher.search(icb='7000')
logger.info("Search results by ICB code")
pp(results)
'''
