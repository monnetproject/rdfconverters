from rdfconverters.xbrl2rdf.xbrl2xebr import XBRL2XEBR

class XBRLFactory:

    @staticmethod
    def from_name(tree, name):
        if name == "es-pgc":
            return XBRLSpanishPGC(tree)
        elif name == "be":
            return XBRLBelgian(tree)

    @staticmethod
    def detect_and_instantiate(tree):
        nsmap = tree.getroot().nsmap
        # Belgian - The 'c' prefix is for corrections to accounts (currently not parsed)
        if 'pfs' in nsmap and not 'c' in nsmap:
            return XBRLBelgian(tree)
        # Spanish pgc07
        if any(map(lambda k: k.startswith('pgc07'), nsmap.keys())):
            return XBRLSpanishPGC(tree)


class XBRLInstance:
    '''
    Abstract class.
    Each implementation is responsible for implementing get_filings_list, which returns a list
    of the filings contained in the XBRL instance.

    The filings should be of the following format:
    {
        'metadata': { 'id': "...", 'start': "yyyy-mm-dd", 'end': "yyyy-mm-dd", 'source': ... },
        'items': { 'hasAssetsTotal': "1234EUR", 'hasEquityTotal': "5678EUR", .... }
    }

    The source attribute should be a tuple with the containing value and uri of a datatype
    '''

    def get_filings_list():
        raise NotImplementedError()

    def __init__(self, xmltree, namespace):
        self.x2x = XBRL2XEBR(namespace)

        self.tree = xmltree
        self.root = self.tree.getroot()
        self.ns = self.root.nsmap

    def _merge_contexts(self, items, contexts):
        '''
        Utility method. items should be a dictionary with an XBRL context id string as its key,
        and a dictionary mapping items to XBRL values as the values. Merges the keys into one
        dictionary.

        >>> x._merge_contexts({'a': {'b': 1}, 'c': {'d': 2}}, ['a', 'b'])
        {'b': 1, 'd': 2}
        '''
        merged = {}
        for context in contexts:
            if context in items:
               merged.update(items[context])
        return merged

    def _prefix(self, s):
        '''Utility method. Convert string containing full URIs to prefixes'''
        for k, v in self.root.nsmap.items():
            s = s.replace("{%s}" % v, k + ':')
        return s

    def _items_to_xebr(self, items):
        '''Utility method. "items" is a dictionary with local XBRL concepts as keys.
        Returns a dictionary with the local XBRL keys replaced by their XEBR equivalent
        (if an exactMatch exists, otherwise it is not inclluded).'''
        items_xebr = {}
        for k, v in items.items():
            k_xebr = self.x2x.get(k)
            if k_xebr is not None:
                items_xebr[k_xebr] = v
        return items_xebr

    def _resolve_unit(self, unit):
        '''Utility method. If unit is a currency code, return the currency name'''
        if unit.startswith("iso4217:"):
            return unit.rsplit(":")[1]
        # Assume unitless otherwise
        return ''

    def _extract_units(self):
        units = {}
        for unit in self.root.findall('./xbrli:unit', namespaces=self.ns):
            key = unit.attrib['id']
            value = unit.find('.//xbrli:measure', namespaces=self.ns).text
            units[key] = self._resolve_unit(value)
        return units

    def _extract_contexts(self):
        contexts = {}
        for context in self.root.findall("./xbrli:context", namespaces=self.ns):
            cid = context.attrib['id']
            contexts[cid] = {}

            x = context.find('.//xbrli:instant', namespaces=self.ns)
            if x is not None:
                contexts[cid]['instant'] = x.text
            else:
                contexts[cid]['start'] = context.find('.//xbrli:startDate', namespaces=self.ns).text
                contexts[cid]['end'] = context.find('.//xbrli:endDate', namespaces=self.ns).text

        return contexts

class XBRLSpanishPGC(XBRLInstance):

    def __init__(self, xbrlfile):
        super().__init__(xbrlfile, "http://www.dfki.de/lt/xbrl_es.owl#")

        self.units = self._extract_units()
        self.contexts = self._extract_contexts()
        self.items = self._extract_data()

        self.previous_items = self._merge_contexts(self.items, ['D.ANTERIOR', 'I.ANTERIOR'])
        self.previous_items_xebr = self._items_to_xebr(self.previous_items)
        self.previous_items_xebr.update(self._extract_company_info('D.ANTERIOR'))
        self.current_items = self._merge_contexts(self.items, ['D.ACTUAL', 'I.ACTUAL'])
        self.current_items_xebr = self._items_to_xebr(self.current_items)
        self.current_items_xebr.update(self._extract_company_info('D.ACTUAL'))

        previous_id = self.root.find('./xbrli:context[@id="I.ANTERIOR"]//xbrli:identifier',
                        namespaces=self.ns).text
        current_id = self.root.find('./xbrli:context[@id="I.ACTUAL"]//xbrli:identifier',
                        namespaces=self.ns).text

        self.previous_filing = {
            'metadata': {
                'id': previous_id,
                'start': self.contexts['D.ANTERIOR']['start'],
                'end': self.contexts['D.ANTERIOR']['end'],
            },
            'items': self.previous_items_xebr
        }

        self.current_filing = {
            'metadata': {
                'id': current_id,
                'start': self.contexts['D.ACTUAL']['start'],
                'end': self.contexts['D.ACTUAL']['end'],
            },
            'items': self.current_items_xebr
        }

    def get_filings_list(self):
        return [self.current_filing, self.previous_filing]

    def _extract_company_info(self, contextRef):
        # Quick'n'dirty solution to manually extract company information
        # (no formal mapping system exists at time of writing)
        idxpath = ".//pgc07mc-apdo0:IdentificacionEmpresaTupla/dgi-est-gen:IdentifierValue[@contextRef='%s']" % contextRef
        idnodechild = self.root.find(idxpath, namespaces=self.ns)
        if idnodechild is not None:
            idnode = idnodechild.getparent()
            def __get(s):
                n = idnode.find(".//"+s, namespaces=self.ns)
                if n is not None:
                    return n.text

            info = {
                'hasCompanyIdValue': __get("dgi-est-gen:IdentifierValue"),
                'hasCompanyNameText': __get("dgi-est-gen:LegalNameValue"),
                'hasCompanyPostcode': __get("dgi-est-gen:ZipPostalCode"),
                'hasCompanyContactPointValue': __get("dgi-est-gen:CommunicationValue")
            }
            for i in range(10):
                x = __get("dgi-lc-es:Xcode_LFC.%.2d" % (i))
                if x is not None:
                    info['hasLegalFormCode'] = "%.2d" % i

            return info
        return {}

    def _extract_data(self):
        items = {}
        # Extract financial data items
        for item in self.root.findall("./*[@contextRef]", namespaces=self.ns):
            key = self._prefix(item.tag)
            cr = item.attrib['contextRef']
            if cr not in items:
                items[cr] = {}
            items[cr][key] = item.text + self.units[item.attrib['unitRef']] # e.g. 100EUR

        return items

    def __str__(self):
        s = "Spanish PGC"
        if hasattr(self, 'current_filing') and self.current_filing:
            s += ' (%s)' % (self.current_filing['metadata']['id'])
        return s



class XBRLBelgian(XBRLInstance):

    def __init__(self, xbrlfile):
        super().__init__(xbrlfile, "http://www.dfki.de/lt/xbrl_be.owl#")

        self.units = self._extract_units()
        self.contexts = self._extract_contexts()
        self.items = self._extract_data()

        self.previous_items = self._merge_contexts(self.items, ['PrecedingDuration', 'PrecedingInstant'])
        self.previous_items_xebr = self._items_to_xebr(self.previous_items)
        self.previous_items_xebr.update(self._extract_company_info('CurrentDuration'))
        self.current_items = self._merge_contexts(self.items, ['CurrentDuration', 'CurrentInstant'])
        self.current_items_xebr = self._items_to_xebr(self.current_items)
        self.current_items_xebr.update(self._extract_company_info('CurrentDuration'))

        previous_id = self.root.find('./xbrli:context[@id="PrecedingInstant"]//xbrli:identifier',
                        namespaces=self.ns)
        current_id = self.root.find('./xbrli:context[@id="CurrentInstant"]//xbrli:identifier',
                        namespaces=self.ns)

        if previous_id is not None:
           self.previous_filing = {
               'metadata': {
                   'id': previous_id.text,
                   'start': self.contexts['PrecedingDuration']['start'],
                   'end': self.contexts['PrecedingDuration']['end'],
                   'source': ("www.fgov.be", 'http://www.w3.org/2001/XMLSchema#anyURI')
               },
               'items': self.previous_items_xebr
           }
        else:
          self.previous_filing = None

        if current_id is not None:
           self.current_filing = {
               'metadata': {
                   'id': current_id.text,
                   'start': self.contexts['CurrentDuration']['start'],
                   'end': self.contexts['CurrentDuration']['end'],
                   'source': ("www.fgov.be", 'http://www.w3.org/2001/XMLSchema#anyURI')
               },
               'items': self.current_items_xebr
           }
        else:
          self.current_filing = None

    def get_filings_list(self):
        return [f for f in [self.current_filing, self.previous_filing] if f is not None]

    def _extract_company_info(self, contextRef):
        # Quick'n'dirty solution to manually extract company information
        # (no formal mapping system exists at time of writing)
        def __get(s):
            n = self.root.find(".//%s[@contextRef='%s']" % (s, contextRef), namespaces=self.ns)
            if n is not None:
                return n.text

        info = {
            'hasCompanyIdValue': __get("pfs-gcd:IdentifierValue"),
            'hasCompanyNameText': __get("pfs-gcd:EntityCurrentLegalName"),
            'hasLegalFormCode': __get('pfs-gcd:EntityForm/*')
        }

        return info

    def _extract_data(self):
        items = {}
        # Extract financial data items
        for item in self.root.findall("./*[@contextRef]", namespaces=self.ns):
            key = self._prefix(item.tag)
            cr = item.attrib['contextRef']
            if cr not in items:
                items[cr] = {}
            if 'unitRef' in item.attrib:
                items[cr][key] = item.text + self.units[item.attrib['unitRef']] # e.g. 100EUR

        return items

    def __str__(self):
        s = "Belgian GAAP"
        if hasattr(self, 'current_filing') and self.current_filing:
            s += ' (%s)' % (self.current_filing['metadata']['id'])
        return s
