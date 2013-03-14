from rdfconverters.xbrl2rdf.xbrl2xebr import XBRL2XEBR
from rdfconverters.util import NS
from lxml import etree
from pprint import pprint as pp

class XBRLFactory:

    @staticmethod
    def from_named_taxonomy(tree, name):
        if name == "es-cnmv":
            return XBRLSpainCNMV(tree)
        if name == "es-pgc":
            return XBRLSpainPGC(tree)
        elif name == "be":
            return XBRLBelgium(tree)

    @staticmethod
    def from_autodetected(tree):
        nsmap = tree.getroot().nsmap
        # Belgian - The 'c' prefix is for corrections to accounts (currently not parsed)
        if 'pfs' in nsmap and not 'c' in nsmap:
            return XBRLBelgium(tree)
        # Spanish CNMV
        if 'ipp-gen' in nsmap:
            return XBRLSpainCNMV(tree)
        # Spanish pgc07
        if any(map(lambda k: k.startswith('pgc07'), nsmap.keys())):
            return XBRLSpainPGC(tree)


class XBRLReport:
    """
    (Abstract class)

    Each XBRLReport represents an XBRL instance file. Each XBRL instance file has zero or
    more filings. Each filing consists of a dictionary of item names and values
    belonging to one or more XBRL contexts.

    Each implementation of XBRLReport must implement get_identifier, which uniquely identifies the
    company (can generally be obtained through an XPath expression), and extract_company_info,
    which extracts xEBR fields such as company name, address (which have no formal mapping system
    at the time of writing). Note: "hasCompanyAddressCountry" should just be the ISO-3166-1 country
    code.

    Filings are of the following format:
    {
        'metadata': {
            'id': "...",
            'start': "yyyy-mm-dd",
            'end': "yyyy-mm-dd",
            'taxonomy': ...,
            'source': ...,
            'is_previous': ...,
        },
        'items': { 'hasAssetsTotal': "1234EUR", 'hasEquityTotal': "5678EUR", .... }
    }

    - 'id' should be a unique identifier for the company.
    - The "source" attribute is optional, but can contain a tuple with the
      containing value and uri of a datatype (e.g. xsd:anyURI)
    - The "is_previous" attribute is a boolean that indicates whether the filing is the latest one
      in the report. For example, if a report contains filings for 2010 and 2011, is_previous
      should be True for 2010 and False for 2011.
    """

    def get_identifier(self): raise NotImplementedError()
    def extract_company_info(self): raise NotImplementedError()

    def __init__(self, xmltree, source_taxonomy, only_year_boundaries=False):
        self.source_taxonomy = source_taxonomy
        self.root = xmltree.getroot()
        self.ns = self.root.nsmap

        self.filings = None

        self.units = self.__extract_units()
        self.contexts = self.__extract_contexts(only_year_boundaries)
        self.items = self.__extract_financial_items()

        self.x2x = XBRL2XEBR(source_taxonomy)

    def parse_filings(self):
        filings = []
        identifier = self.get_identifier()
        company_info = self.extract_company_info()

        # Figure out contexts by date
        by_end = self._get_contexts_by_end()
        by_end_ordered_keys = sorted(by_end)

        for key in by_end_ordered_keys:
            contexts = by_end[key]
            filing = self._create_filing(contexts, identifier, is_previous=(key!=by_end_ordered_keys[-1]))
            if(filing) is not None:
                filing['items'].update(company_info)
                filings.append(filing)

        self.filings = filings

    def get_filings_list(self):
        return self.filings

    def __extract_contexts(self, only_year_boundaries):
        '''
        Returns a dictionary of XBRL contexts with the context id attribute as a key and
        either instant or start/end dates.
        '''
        contexts = {}
        for context in self.root.findall("./{http://www.xbrl.org/2003/instance}context", namespaces=self.ns):
            c = {}

            instant = context.find('.//{http://www.xbrl.org/2003/instance}instant', namespaces=self.ns)
            if instant is not None:
                c['instant'] = instant.text
            else:
                c['start'] = context.find('.//{http://www.xbrl.org/2003/instance}startDate', namespaces=self.ns).text
                c['end'] = context.find('.//{http://www.xbrl.org/2003/instance}endDate', namespaces=self.ns).text

            if (not only_year_boundaries) or c.get('instant','').endswith("12-31") or (c.get('start','').endswith("01-01") and c.get('end','').endswith("12-31")):
                contexts[context.attrib['id']] = c

        return contexts

    def __extract_units(self):
        units = {}
        for unit in self.root.findall('./{http://www.xbrl.org/2003/instance}unit', namespaces=self.ns):
            key = unit.attrib['id']

            # Extract currency code as value or empty for pure units
            mesaure_text = unit.find('.//{http://www.xbrl.org/2003/instance}measure', namespaces=self.ns).text
            measure = mesaure_text.rsplit(":")[1] if mesaure_text.startswith("iso4217:") else ''
            units[key] = measure
        return units

    def __extract_financial_items(self):
        items = {}
        for item in (i for i in self.root.iter(tag=etree.Element) if 'contextRef' in i.attrib):
            tag_name = self._expanded_xml_tag_to_prefixed(item.tag)
            context_ref = item.attrib['contextRef']
            if context_ref not in items:
                items[context_ref] = {}
            if 'unitRef' in item.attrib:
                iso4217_currency = self.units[item.attrib['unitRef']]
                monetary_value = self._normalise_decimal_value(item.attrib['decimals'], item.text)
                items[context_ref][tag_name] = monetary_value + iso4217_currency

        return items

    def _normalise_decimal_value(self, decimals_str, value):
        '''Utility method, accounts for the @decimals attribute of a financial item'''
        try:
            decimals = int(decimals_str)
        except ValueError:
            return value

        if decimals < 0:
            return value[:decimals]
        else:
            return value

    def _humanize_name(self, name):
        '''Utility method, cleans up company names'''
        if len(name)<=4: # Ignore probable abbreviations
            return name
        if name.isupper():
            return name.title()
        return name

    def _expanded_xml_tag_to_prefixed(self, s):
        '''Utility method. Convert string containing expanded XML URI to its xmlns name'''
        for k, v in self.root.nsmap.items():
            prefix = "{%s}" % v
            if s.startswith(prefix):
                return s.replace(prefix, k + ':')
        return s

    def _items_in_contexts(self, *contexts):
        '''
        Utility method. Returns a dictionary of items to values with the given contexts.
        '''
        merged = {}
        for context in contexts:
            if context in self.items:
                merged.update(self.items[context])
        return merged

    def _items_to_xebr(self, items, namespace):
        '''Utility method. "items" is a dictionary with local XBRL concepts as keys.
        Returns a dictionary with the local XBRL keys replaced by their XEBR equivalent
        (if an exactMatch exists, otherwise it is not inclluded).'''
        items_xebr = {}
        for k, v in items.items():
            k_xebr = self.x2x.get(k)
            if k_xebr is not None:
                items_xebr[k_xebr] = v
        return items_xebr

    def _get_contexts_by_end(self):
        '''Utility method. Get a dictionary of context names with keys as instant or end date'''

        by_end = {}
        for name, data in self.contexts.items():
            date = data['instant'] if 'instant' in data else data['end']
            if not date in by_end:
                by_end[date] = []
            by_end[date].append(name)
        return by_end


    def _create_filing(self, contexts, identifier, is_previous=False, source=None):
        '''Utility method to construct a filing in the expected format.'''
        items = self._items_in_contexts(*contexts)
        items_xebr = self._items_to_xebr(items, "http://www.dfki.de/lt/xbrl_be.owl#")

        # Get start date from contexts
        for context in contexts:
            if 'start' in self.contexts[context]:
                start = self.contexts[context]['start']
                break
        else:
            return None
        # Get end date from contexts
        for context in contexts:
            if 'end' in self.contexts[context]:
                end = self.contexts[context]['end']
                break
        else:
            return None

        filing = {
            'metadata': {
                'id': identifier,
                'start': start,
                'taxonomy': self.source_taxonomy,
                'end': end,
                'is_previous': is_previous
            },
            'items': items_xebr
        }
        filing['items']['hasCompanyIdValue'] = identifier

        if source is not None:
            filing['metadata']['source'] = source

        return filing


class XBRLBelgium(XBRLReport):

    def __init__(self, xmltree):
        super().__init__(xmltree, "http://www.dfki.de/lt/xbrl_be.owl#")

    def get_identifier(self):
        identifier = self.root.find(".//pfs-gcd:EntityInformation//pfs-gcd:IdentifierValue",
            namespaces=self.ns).text
        return identifier

    def extract_company_info(self):
        def __get(s):
            n = self.root.find(".//%s[@contextRef='CurrentDuration']" % (s), namespaces=self.ns)
            if n is not None:
                return n.text
            raise Exception("Couldn't find " + s)

        info = {
            'hasCompanyIdValue': __get("pfs-gcd:EntityInformation//pfs-gcd:IdentifierValue"),
            'hasCompanyNameText': self._humanize_name(__get("pfs-gcd:EntityInformation//pfs-gcd:EntityCurrentLegalName")),
            'hasLegalFormCode': __get('pfs-gcd:EntityForm/*'),
        }
        try:
            country_code = self.root.find(".//pfs-gcd:EntityInformation/pfs-gcd:EntityAddress/pfs-gcd:CountryCode", namespaces=self.ns).getchildren()[0].text

            info['hasCompanyAddressCountry'] = NS['if'][country_code.strip().upper()]
        except Exception as e:
            print("Getting country code failed:", str(e))

        return info

    def __str__(self):
        return "Belgium GAAP"

class XBRLSpainPGC(XBRLReport):

    def __init__(self, xmltree):
        super().__init__(xmltree, "http://www.dfki.de/lt/xbrl_es.owl#")

    def get_identifier(self):
        id_expression = ".//dgi-est-gen:IdentifierCode/dgi-est-gen:IdentifierValue"
        identifier = self.root.find(id_expression, namespaces=self.ns).text
        return identifier

    def extract_company_info(self):
        def __get(s):
            xpath_prefix = './/pgc07mc-apdo0:IdentificacionEmpresaTupla/'
            n = self.root.find(xpath_prefix+s, namespaces=self.ns)
            if n is not None:
                return n.text
            raise Exception("Couldn't find " + s)

        info = {
            'hasCompanyNameText': self._humanize_name(__get("dgi-est-gen:LegalNameValue")),
            'hasCompanyPostcode': __get("dgi-est-gen:ZipPostalCode"),
            'hasCompanyContactPointValue': __get("dgi-est-gen:CommunicationValue"),
        }

        for i in range(10):
            x = __get("dgi-lc-es:Xcode_LFC.%.2d" % (i))
            if x is not None:
                info['hasLegalFormCode'] = "%.2d" % i

        return info

    def __str__(self):
        return "Spain PGC"


class XBRLSpainCNMV(XBRLReport):

    def __init__(self, xmltree):
        super().__init__(xmltree, "http://www.dfki.de/lt/xbrl_es_cnmv.owl#", only_year_boundaries=True)

    def get_identifier(self):
        id_expression = ".//dgi-est-gen:IdentifierCode/dgi-est-gen:IdentifierValue"
        identifier = self.root.find(id_expression, namespaces=self.ns).text
        return identifier

    def extract_company_info(self):
        def __get(s):
            n = self.root.find('.//'+s, namespaces=self.ns)
            if n is not None:
                return n.text
            raise Exception("Couldn't find " + s)

        info = {
            'hasCompanyNameText': self._humanize_name(__get("dgi-est-gen:LegalName/dgi-est-gen:LegalNameValue")),
            'hasCompanyAddressCountry': NS['if']['ES']
        }

        return info

    def __str__(self):
        return "Spain CNMV"
