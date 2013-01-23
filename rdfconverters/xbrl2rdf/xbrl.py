from rdfconverters.xbrl2rdf.xbrl2xebr import XBRL2XEBR

class XBRLFactory:

    @staticmethod
    def from_named_taxonomy(tree, name):
        if name == "es-pgc":
            pass#return XBRLSpanishPGC(tree)
        elif name == "be":
            pass#return XBRLBelgian(tree)

    @staticmethod
    def from_autodetected(tree):
        nsmap = tree.getroot().nsmap
        # Belgian - The 'c' prefix is for corrections to accounts (currently not parsed)
        if 'pfs' in nsmap and not 'c' in nsmap:
            return XBRLBelgium(tree)
        # Spanish CNMV
        if 'ipp-gen' in nsmap:
            pass#return XBRLSpanishCNMV(tree)
        # Spanish pgc07
        if any(map(lambda k: k.startswith('pgc07'), nsmap.keys())):
            return XBRLSpainPGC(tree)


class XBRLReport:
    """
    (Abstract class)

    Each XBRLReport represents an XBRL instance file. Each XBRL instance file has zero or
    more filings. Each filing consists of a dictionary of item names and values
    belonging to one or more XBRL contexts.

    Each implementation of XBRLReport must implement parse_filings, which sets the self.filings
    list.

    The filings should be of the following format:
    {
        'metadata': {
            'id': "...",
            'start': "yyyy-mm-dd",
            'end': "yyyy-mm-dd",
            'source': ...
            'is_previous': ...
        },
        'items': { 'hasAssetsTotal': "1234EUR", 'hasEquityTotal': "5678EUR", .... }
    }

    The _make_filing utility method assists in constructing this.

    - 'id' should be an ISIN (or at least it is in all the reports we have available).
    - The "source" attribute is optional, but can contain a tuple with the
      containing value and uri of a datatype (e.g. xsd:anyURI)
    - The "is_previous" attribute is a boolean that indicates whether the filing is the latest one
      in the report. For example, if a report contains filings for 2010 and 2011, is_previous
      should be True for 2010 and False for 2011.

    """

    def __init__(self, xmltree, xebr_namespace):
        self.root = xmltree.getroot()
        self.ns = self.root.nsmap

        self.filings = None

        self.units = self.__extract_units()
        self.contexts = self.__extract_contexts()
        self.items = self.__extract_financial_items()

        self.x2x = XBRL2XEBR(xebr_namespace)

    def parse_filings(self):
        raise NotImplementedError()

    def get_filings_list(self):
        return self.filings

    def __extract_contexts(self):
        '''
        Returns a dictionary of XBRL contexts with the context id attribute as a key and
        either instant or start/end dates.
        '''
        contexts = {}
        for context in self.root.findall("./xbrli:context", namespaces=self.ns):
            c = contexts[context.attrib['id']] = {}

            instant = context.find('.//xbrli:instant', namespaces=self.ns)
            if instant is not None:
                c['instant'] = instant.text
            else:
                c['start'] = context.find('.//xbrli:startDate', namespaces=self.ns).text
                c['end'] = context.find('.//xbrli:endDate', namespaces=self.ns).text

        return contexts

    def __extract_units(self):
        units = {}
        for unit in self.root.findall('./xbrli:unit', namespaces=self.ns):
            key = unit.attrib['id']

            # Extract currency code as value or empty for pure units
            mesaure_text = unit.find('.//xbrli:measure', namespaces=self.ns).text
            measure = mesaure_text.rsplit(":")[1] if mesaure_text.startswith("iso4217:") else ''
            units[key] = measure
        return units

    def __extract_financial_items(self):
        items = {}
        for item in self.root.findall("./*[@contextRef]", namespaces=self.ns):
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
            raise Exception("Start date not found in contexts %s" % contexts)
        # Get end date from contexts
        for context in contexts:
            if 'end' in self.contexts[context]:
                end = self.contexts[context]['end']
                break
        else:
            raise Exception("End date not found in contexts %s" % contexts)

        filing = {
            'metadata': {
                'id': identifier,
                'start': start,
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


    def parse_filings(self):
        identifier = self.root.find(".//pfs-gcd:EntityInformation//pfs-gcd:IdentifierValue",
            namespaces=self.ns).text
        src = ("www.fgov.be", 'http://www.w3.org/2001/XMLSchema#anyURI')
        company_info = self._extract_company_info()

        filings = []

        if 'PrecedingDuration' in self.contexts:
            previous_filing = self._create_filing(['PrecedingDuration', 'PrecedingInstant'], identifier,
                is_previous=True, source=src)
            previous_filing['items'].update(company_info)
            filings.append(previous_filing)

        current_filing = self._create_filing(['CurrentDuration', 'CurrentInstant'], identifier, source=src)
        current_filing['items'].update(company_info)
        filings.append(current_filing)

        self.filings = filings

    def _extract_company_info(self):
        def __get(s):
            n = self.root.find(".//%s[@contextRef='CurrentDuration']" % (s), namespaces=self.ns)
            if n is not None:
                return n.text
            raise Exception("Couldn't find " + s)

        info = {
            'hasCompanyIdValue': __get("pfs-gcd:EntityInformation//pfs-gcd:IdentifierValue"),
            'hasCompanyNameText': self._humanize_name(__get("pfs-gcd:EntityInformation//pfs-gcd:IdentifierValue")),
            'hasLegalFormCode': __get('pfs-gcd:EntityForm/*')
        }
        return info

    def __str__(self):
        return "Belgium GAAP"

class XBRLSpainPGC(XBRLReport):

    def __init__(self, xmltree):
        super().__init__(xmltree, "http://www.dfki.de/lt/xbrl_es.owl#")

    def parse_filings(self):
        identifier = self.root.find(".//pgc07mc-apdo0:IdentificacionEmpresaTupla/dgi-est-gen:IdentifierValue[@contextRef='D.ACTUAL']",
            namespaces=self.ns).text
        company_info = self._extract_company_info()

        filings = []
        if 'D.ANTERIOR' in self.contexts:
            previous_filing = self._create_filing(['D.ANTERIOR', 'I.ANTERIOR'], identifier, is_previous=True)
            previous_filing['items'].update(company_info)
            filings.append(previous_filing)

        current_filing = self._create_filing(['D.ACTUAL', 'I.ACTUAL'], identifier)
        current_filing['items'].update(company_info)
        filings.append(current_filing)

        self.filings = filings

    def _extract_company_info(self):
        def __get(s):
            xpath_prefix = './/pgc07mc-apdo0:IdentificacionEmpresaTupla/'
            n = self.root.find(xpath_prefix+s, namespaces=self.ns)
            if n is not None:
                return n.text

        info = {
            'hasCompanyNameText': self._humanize_name(__get("dgi-est-gen:LegalNameValue")),
            'hasCompanyPostcode': __get("dgi-est-gen:ZipPostalCode"),
            'hasCompanyContactPointValue': __get("dgi-est-gen:CommunicationValue")
        }
        for i in range(10):
            x = __get("dgi-lc-es:Xcode_LFC.%.2d" % (i))
            if x is not None:
                info['hasLegalFormCode'] = "%.2d" % i

        return info

    def __str__(self):
        return "Spain PGC"
