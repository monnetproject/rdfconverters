class RDFUtil:
    @staticmethod
    def uri_to_concept(uri):
        return uri.rsplit("#")[1]

    @staticmethod
    def rdf_name_to_xml_name(rdf_name):
        rdf_name = rdf_name.rsplit("#")[1]
        rdf_name = rdf_name.replace('_', ':', 1).replace(':has', ':', 1)
        return rdf_name
