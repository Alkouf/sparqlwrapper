# -*- coding: utf-8 -*-
#!/usr/bin/python

import inspect
import os
import sys
import logging
import unittest

# prefer local copy to the one which is installed
# hack from http://stackoverflow.com/a/6098238/280539
_top_level_path = os.path.realpath(os.path.abspath(os.path.join(
    os.path.split(inspect.getfile(inspect.currentframe()))[0],
    ".."
)))
if _top_level_path not in sys.path:
    sys.path.insert(0, _top_level_path)
# end of hack

import warnings
warnings.simplefilter("always")

try:
    from rdflib.graph import ConjunctiveGraph
except ImportError:
    from rdflib import ConjunctiveGraph
from SPARQLWrapper import SPARQLWrapper, XML, RDFXML, N3, TURTLE, JSONLD, JSON, CSV, TSV, POST, GET, SELECT, CONSTRUCT, ASK, DESCRIBE
from SPARQLWrapper.Wrapper import _SPARQL_XML, _SPARQL_JSON, _XML, _RDF_XML, _RDF_N3, _RDF_JSONLD, _CSV, _TSV
from SPARQLWrapper.SPARQLExceptions import QueryBadFormed

_SPARQL_SELECT_ASK_POSSIBLE = _SPARQL_XML + _SPARQL_JSON + _CSV + _TSV + _XML # only used in test
_SPARQL_DESCRIBE_CONSTRUCT_POSSIBLE = _RDF_XML + _RDF_N3 + _XML + _RDF_JSONLD # only used in test. Same as Wrapper._RDF_POSSIBLE

try:
    from urllib.error import HTTPError   # Python 3
except ImportError:
    from urllib2 import HTTPError        # Python 2

try:
    bytes   # Python 2.6 and above
except NameError:
    bytes = str

logging.basicConfig()

endpoint = "http://sparql.agroportal.lirmm.fr/sparql/" # 4store SPARQL server v1.1.5-122-g1788d29

prefixes = """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
"""

selectQuery = """
    SELECT DISTINCT ?s WHERE {
         ?s a ?o .
         VALUES ?o {<http://id.agrisemantics.org/vocab#Organism>}
    } LIMIT 100
"""

selectQueryCSV_TSV = """
    SELECT DISTINCT ?s ?o WHERE {
         ?s a ?o .
         VALUES ?o {<http://id.agrisemantics.org/vocab#Organism>}
    } LIMIT 100
 """
askQuery = """
    ASK { <http://id.agrisemantics.org/gacs/C29647> a ?type }
"""

constructQuery = """
    CONSTRUCT {
        _:v skos:prefLabel ?label .
        _:v rdfs:comment "this is only a mock node to test library"
    }
    WHERE {
        <http://id.agrisemantics.org/gacs/C29647> skos:prefLabel ?label .
    }
"""

describeQuery = """
    DESCRIBE <http://id.agrisemantics.org/gacs/C29647>
"""

queryBadFormed = """
    PREFIX prop: <http://dbpedia.org/property/>
    PREFIX res: <http://dbpedia.org/resource/>
    FROM <http://dbpedia.org/sparql?default-graph-uri=http%3A%2F%2Fdbpedia.org&should-sponge=&query=%0D%0ACONSTRUCT+%7B%0D%0A++++%3Chttp%3A%2F%2Fdbpedia.org%2Fresource%2FBudapest%3E+%3Fp+%3Fo.%0D%0A%7D%0D%0AWHERE+%7B%0D%0A++++%3Chttp%3A%2F%2Fdbpedia.org%2Fresource%2FBudapest%3E+%3Fp+%3Fo.%0D%0A%7D%0D%0A&format=application%2Frdf%2Bxml>
    SELECT ?lat ?long
    WHERE {
        res:Budapest prop:latitude ?lat;
        prop:longitude ?long.
    }      
"""

queryManyPrefixes = """
    PREFIX conf: <http://richard.cyganiak.de/2007/pubby/config.rdf#>
    PREFIX meta: <http://example.org/metadata#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX dc: <http://purl.org/dc/elements/1.1/>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>
    PREFIX dbpedia: <http://dbpedia.org/resource/>
    PREFIX o: <http://dbpedia.org/ontology/>
    PREFIX p: <http://dbpedia.org/property/>
    PREFIX yago: <http://dbpedia.org/class/yago/>
    PREFIX units: <http://dbpedia.org/units/>
    PREFIX geonames: <http://www.geonames.org/ontology#>
    PREFIX prv: <http://purl.org/net/provenance/ns#>
    PREFIX prvTypes: <http://purl.org/net/provenance/types#>
    PREFIX foo: <http://purl.org/foo>

    SELECT ?label
    WHERE {
        <http://dbpedia.org/resource/Asturias> rdfs:label ?label .
    }
"""

queryDuplicatedPrefix = """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT ?s ?p ?o WHERE {
        ?s ?p ?o .
    } LIMIT 10
"""

queryWithCommaInCurie_1 = """
    PREFIX dbpedia: <http://dbpedia.org/resource/>
    SELECT ?article ?title WHERE {
        ?article ?relation dbpedia:Victoria\\,\\_British\\_Columbia .
        ?article <http://xmlns.com/foaf/0.1/isPrimaryTopicOf> ?title
    }
"""

queryWithCommaInCurie_2 = """
    PREFIX dbpedia: <http://dbpedia.org/resource/>
    SELECT ?article ?title WHERE {
        ?article ?relation dbpedia:Category\:Victoria\,\_British\_Columbia .
        ?article <http://xmlns.com/foaf/0.1/isPrimaryTopicOf> ?title
    }
"""

queryWithCommaInUri = """
    SELECT ?article ?title WHERE {
        ?article ?relation <http://dbpedia.org/resource/Category:Victoria,_British_Columbia> .
        ?article <http://xmlns.com/foaf/0.1/isPrimaryTopicOf> ?title
    }
"""

class SPARQLWrapperTests(unittest.TestCase):

    def __generic(self, query, returnFormat, method, onlyConneg=False): # 4store uses URL parameters or conneg.
        sparql = SPARQLWrapper(endpoint)
        sparql.setQuery(prefixes + query)
        sparql.setReturnFormat(returnFormat)
        sparql.setMethod(method)
        sparql.setOnlyConneg(onlyConneg)
        try:
            result = sparql.query()
        except HTTPError:
            # An ugly way to get the exception, but the only one that works
            # both on Python 2.5 and Python 3.
            e = sys.exc_info()[1]
            if e.code == 400:
                sys.stdout.write("400 Bad Request, probably query is not well formed")
            elif e.code == 406:
                sys.stdout.write("406 Not Acceptable, maybe query is not well formed")
            else:
                sys.stdout.write(str(e))
            sys.stdout.write("\n")
            return False
        else:
            return result


################################################################################
################################################################################

################
#### SELECT ####
################

    def testSelectByGETinXML(self):
        result = self.__generic(selectQuery, XML, GET)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _SPARQL_XML], ct
        results = result.convert()
        results.toxml()
        self.assertEqual(results.__class__.__module__, "xml.dom.minidom")
        self.assertEqual(results.__class__.__name__, "Document")

    def testSelectByPOSTinXML(self):
        result = self.__generic(selectQuery, XML, POST)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _SPARQL_XML], ct
        results = result.convert()
        results.toxml()
        self.assertEqual(results.__class__.__module__, "xml.dom.minidom")
        self.assertEqual(results.__class__.__name__, "Document")

    def testSelectByGETinCSV(self):
        result = self.__generic(selectQueryCSV_TSV, CSV, GET)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _CSV], ct
        results = result.convert()
        self.assertEqual(type(results), bytes)

    def testSelectByPOSTinCSV(self):
        result = self.__generic(selectQueryCSV_TSV, CSV, POST)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _CSV], ct
        results = result.convert()
        self.assertEqual(type(results), bytes)

    @unittest.skip("4store does not support receiving unexpected output values (check Wrapper code for TSV URL generation)")
    def testSelectByGETinTSV(self):
        result = self.__generic(selectQueryCSV_TSV, TSV, GET)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _TSV], ct
        results = result.convert()
        self.assertEqual(type(results), bytes)

    def testSelectByGETinTSVConneg(self):
        result = self.__generic(selectQueryCSV_TSV, TSV, GET, onlyConneg=True)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _TSV], ct
        results = result.convert()
        self.assertEqual(type(results), bytes)

    def testSelectByPOSTinTSV(self):
        result = self.__generic(selectQueryCSV_TSV, TSV, POST)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _TSV], ct
        results = result.convert()
        self.assertEqual(type(results), bytes)

    def testSelectByGETinJSON(self):
        result = self.__generic(selectQuery, JSON, GET)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _SPARQL_JSON], ct
        results = result.convert()
        self.assertEqual(type(results), dict)

    def testSelectByPOSTinJSON(self):
        result = self.__generic(selectQuery, JSON, POST)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _SPARQL_JSON], ct
        results = result.convert()
        self.assertEqual(type(results), dict)

    # asking for an unexpected return format for SELECT queryType (n3 is not supported is an invalid alias). Set by the default None (and sending */*). For a SELECT query type, the default return mimetype (if Accept: */* is sent) is application/sparql-results+xml
    def testSelectByGETinN3Conneg(self):
        result = self.__generic(selectQuery, N3, GET, onlyConneg=True)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _SPARQL_SELECT_ASK_POSSIBLE], ct
        results = result.convert()
        results.toxml()
        self.assertEqual(results.__class__.__module__, "xml.dom.minidom")
        self.assertEqual(results.__class__.__name__, "Document")

    # asking for an unexpected return format for SELECT queryType (n3 is not supported is an invalid alias). Set by the default None (and sending */*). For a SELECT query type, the default return mimetype (if Accept: */* is sent) is application/sparql-results+xml
    def testSelectByPOSTinN3Conneg(self):
        result = self.__generic(selectQuery, N3, POST, onlyConneg=True)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _SPARQL_SELECT_ASK_POSSIBLE], ct
        results = result.convert()
        results.toxml()
        self.assertEqual(results.__class__.__module__, "xml.dom.minidom")
        self.assertEqual(results.__class__.__name__, "Document")

    # asking for an unexpected return format for SELECT queryType (json-ld is not supported is an invalid alias). Set by the default None (and sending */*). For a SELECT query type, the default return mimetype (if Accept: */* is sent) is application/sparql-results+xml
    def testSelectByGETinJSONLDConneg(self):
        result = self.__generic(selectQuery, JSONLD, GET, onlyConneg=True)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _SPARQL_SELECT_ASK_POSSIBLE], ct
        results = result.convert()
        results.toxml()
        self.assertEqual(results.__class__.__module__, "xml.dom.minidom")
        self.assertEqual(results.__class__.__name__, "Document")

    # asking for an unexpected return format for SELECT queryType (json-ld is not supported is an invalid alias). Set by the default None (and sending */*). For a SELECT query type, the default return mimetype (if Accept: */* is sent) is application/sparql-results+xml
    def testSelectByPOSTinJSONLDConneg(self):
        result = self.__generic(selectQuery, JSONLD, POST, onlyConneg=True)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _SPARQL_SELECT_ASK_POSSIBLE], ct
        results = result.convert()
        results.toxml()
        self.assertEqual(results.__class__.__module__, "xml.dom.minidom")
        self.assertEqual(results.__class__.__name__, "Document")

    # asking for an unknown return format for SELECT queryType (XML is sent)
    def testSelectByGETinUnknow(self):
        result = self.__generic(selectQuery, "foo", GET)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _SPARQL_SELECT_ASK_POSSIBLE], ct
        results = result.convert()
        results.toxml()
        self.assertEqual(results.__class__.__module__, "xml.dom.minidom")
        self.assertEqual(results.__class__.__name__, "Document")

    # asking for an unknown return format for SELECT queryType (XML is sent)
    def testSelectByPOSTinUnknow(self):
        result = self.__generic(selectQuery, "bar", POST)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _SPARQL_SELECT_ASK_POSSIBLE], ct
        results = result.convert()
        results.toxml()
        self.assertEqual(results.__class__.__module__, "xml.dom.minidom")
        self.assertEqual(results.__class__.__name__, "Document")

################################################################################
################################################################################

#############
#### ASK ####
#############

    def testAskByGETinXML(self):
        result = self.__generic(askQuery, XML, GET)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _SPARQL_XML], ct
        results = result.convert()
        results.toxml()
        self.assertEqual(results.__class__.__module__, "xml.dom.minidom")
        self.assertEqual(results.__class__.__name__, "Document")

    def testAskByPOSTinXML(self):
        result = self.__generic(askQuery, XML, POST)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _SPARQL_XML], ct
        results = result.convert()
        results.toxml()
        self.assertEqual(results.__class__.__module__, "xml.dom.minidom")
        self.assertEqual(results.__class__.__name__, "Document")

    def testAskByGETinCSV(self):
        result = self.__generic(askQuery, CSV, GET)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _CSV], ct
        results = result.convert()

    def testAskByPOSTinCSV(self):
        result = self.__generic(askQuery, CSV, POST)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _CSV], ct
        results = result.convert()

    @unittest.skip("TSV is supported for 4store, but it returns a text/plain instead of text/tab-separated-values")
    def testAskByGETinTSV(self):
        result = self.__generic(askQuery, TSV, GET)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _TSV], ct
        results = result.convert()

    def testAskByGETinTSVConneg(self):
        result = self.__generic(askQuery, TSV, GET, onlyConneg=True)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _TSV], ct
        results = result.convert()
        self.assertEqual(type(results), bytes)

    def testAskByPOSTinTSV(self):
        result = self.__generic(askQuery, TSV, POST)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _TSV], ct
        results = result.convert()

    def testAskByGETinJSON(self):
        result = self.__generic(askQuery, JSON, GET)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _SPARQL_JSON], ct
        results = result.convert()
        self.assertEqual(type(results), dict)

    def testAskByPOSTinJSON(self):
        result = self.__generic(askQuery, JSON, POST)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _SPARQL_JSON], ct
        results = result.convert()
        self.assertEqual(type(results), dict)

    # asking for an unexpected return format for ASK queryType (n3 is not supported is an invalid alias). Set by the default None (and sending */*). For a SELECT query type, the default return mimetype (if Accept: */* is sent) is application/sparql-results+xml
    def testAskByGETinN3Conneg(self):
        result = self.__generic(askQuery, N3, GET, onlyConneg=True)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _SPARQL_SELECT_ASK_POSSIBLE], ct
        results = result.convert()
        results.toxml()
        self.assertEqual(results.__class__.__module__, "xml.dom.minidom")
        self.assertEqual(results.__class__.__name__, "Document")

    # asking for an unexpected return format for ASK queryType (n3 is not supported is an invalid alias). Set by the default None (and sending */*). For a SELECT query type, the default return mimetype (if Accept: */* is sent) is application/sparql-results+xml
    def testAskByPOSTinN3Conneg(self):
        result = self.__generic(askQuery, N3, POST, onlyConneg=True)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _SPARQL_SELECT_ASK_POSSIBLE], ct
        results = result.convert()
        results.toxml()
        self.assertEqual(results.__class__.__module__, "xml.dom.minidom")
        self.assertEqual(results.__class__.__name__, "Document")

    # asking for an unexpected return format for ASK queryType (json-ld is not supported is an invalid alias). Set by the default None (and sending */*). For a SELECT query type, the default return mimetype (if Accept: */* is sent) is application/sparql-results+xml
    def testAskByGETinJSONLDConneg(self):
        result = self.__generic(askQuery, JSONLD, GET, onlyConneg=True)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _SPARQL_SELECT_ASK_POSSIBLE], ct
        results = result.convert()
        results.toxml()
        self.assertEqual(results.__class__.__module__, "xml.dom.minidom")
        self.assertEqual(results.__class__.__name__, "Document")

    # asking for an unexpected return format for ASK queryType (json-ld is not supported is an invalid alias). Set by the default None (and sending */*). For a SELECT query type, the default return mimetype (if Accept: */* is sent) is application/sparql-results+xml
    def testAskByPOSTinJSONLDConneg(self):
        result = self.__generic(askQuery, JSONLD, POST, onlyConneg=True)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _SPARQL_SELECT_ASK_POSSIBLE], ct
        results = result.convert()
        results.toxml()
        self.assertEqual(results.__class__.__module__, "xml.dom.minidom")
        self.assertEqual(results.__class__.__name__, "Document")

    # asking for an unknown return format for ASK queryType (XML is sent)
    def testAskByGETinUnknow(self):
        result = self.__generic(askQuery, "foo", GET)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _SPARQL_SELECT_ASK_POSSIBLE], ct
        results = result.convert()
        results.toxml()
        self.assertEqual(results.__class__.__module__, "xml.dom.minidom")
        self.assertEqual(results.__class__.__name__, "Document")

    # asking for an unknown return format for ASK queryType (XML is sent)
    def testAskByPOSTinUnknow(self):
        result = self.__generic(askQuery, "bar", POST)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _SPARQL_SELECT_ASK_POSSIBLE], ct
        results = result.convert()
        results.toxml()
        self.assertEqual(results.__class__.__module__, "xml.dom.minidom")
        self.assertEqual(results.__class__.__name__, "Document")

################################################################################
################################################################################

###################
#### CONSTRUCT ####
###################

    def testConstructByGETinXML(self):
        result = self.__generic(constructQuery, XML, GET)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _RDF_XML], ct
        results = result.convert()
        self.assertEqual(type(results), ConjunctiveGraph)

    def testConstructByPOSTinXML(self):
        result = self.__generic(constructQuery, XML, POST)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _RDF_XML], ct
        results = result.convert()
        self.assertEqual(type(results), ConjunctiveGraph)

    # rdf+xml is not a valid alias
    def testConstructByGETinRDFXMLConneg(self):
        result = self.__generic(constructQuery, RDFXML, GET, onlyConneg=True)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _RDF_XML], ct
        results = result.convert()
        self.assertEqual(type(results), ConjunctiveGraph)

    # rdf+xml is not a valid alias
    def testConstructByPOSTinRDFXMLConneg(self):
        result = self.__generic(constructQuery, RDFXML, POST, onlyConneg=True)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _RDF_XML], ct
        results = result.convert()
        self.assertEqual(type(results), ConjunctiveGraph)

    # turtle is not a valid alias (text is the one used)
    def testConstructByGETinTurtleConneg(self):
        result = self.__generic(constructQuery, TURTLE, GET, onlyConneg=True)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _RDF_N3], ct
        results = result.convert()
        self.assertEqual(type(results), bytes)

    # turtle is not a valid alias (text is the one used)
    def testConstructByPOSTinTurtleConneg(self):
        result = self.__generic(constructQuery, TURTLE, POST, onlyConneg=True)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _RDF_N3], ct
        results = result.convert()
        self.assertEqual(type(results), bytes)

    @unittest.skip("JSON-LD is not currently supported")
    def testConstructByGETinJSONLD(self):
        result = self.__generic(constructQuery, JSONLD, GET)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _RDF_JSONLD], ct
        results = result.convert()
        self.assertEqual(type(results), ConjunctiveGraph)

    @unittest.skip("JSON-LD is not currently supported")
    def testConstructByPOSTinJSONLD(self):
        result = self.__generic(constructQuery, JSONLD, POST)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _RDF_JSONLD], ct
        results = result.convert()
        self.assertEqual(type(results), ConjunctiveGraph)

    # asking for an unexpected return format for CONSTRUCT queryType. For a CONSTRUCT query type, the default return mimetype (if Accept: */* is sent) is application/rdf+xml
    def testConstructByGETinCSVConneg(self):
        result = self.__generic(constructQuery, CSV, GET, onlyConneg=True)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _SPARQL_DESCRIBE_CONSTRUCT_POSSIBLE], "returned Content-Type='%s'. Expected fail due to Virtuoso configuration" %(ct)
        results = result.convert()
        self.assertEqual(type(results), ConjunctiveGraph)

    # asking for an unexpected return format for CONSTRUCT queryType. For a CONSTRUCT query type, the default return mimetype (if Accept: */* is sent) is application/rdf+xml
    def testConstructByPOSTinCSVConneg(self):
        result = self.__generic(constructQuery, CSV, POST, onlyConneg=True)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _SPARQL_DESCRIBE_CONSTRUCT_POSSIBLE], "returned Content-Type='%s'. Expected fail due to Virtuoso configuration" %(ct)
        results = result.convert()
        self.assertEqual(type(results), ConjunctiveGraph)

    # asking for an unknown return format for CONSTRUCT queryType (XML is sent)
    def testConstructByGETinUnknow(self):
        result = self.__generic(constructQuery, "foo", GET)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _SPARQL_DESCRIBE_CONSTRUCT_POSSIBLE], ct
        results = result.convert()
        self.assertEqual(type(results), ConjunctiveGraph)

    # asking for an unknown return format for CONSTRUCT queryType (XML is sent)
    def testConstructByPOSTinUnknow(self):
        result = self.__generic(constructQuery, "bar", POST)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _SPARQL_DESCRIBE_CONSTRUCT_POSSIBLE], ct
        results = result.convert()
        self.assertEqual(type(results), ConjunctiveGraph)

################################################################################
################################################################################

##################
#### DESCRIBE ####
##################

    def testDescribeByGETinXML(self):
        result = self.__generic(describeQuery, XML, GET)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _RDF_XML], ct
        results = result.convert()
        self.assertEqual(type(results), ConjunctiveGraph)

    def testDescribeByPOSTinXML(self):
        result = self.__generic(describeQuery, XML, POST)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _RDF_XML], ct
        results = result.convert()
        self.assertEqual(type(results), ConjunctiveGraph)

    # rdf+xml is not a valid alias
    def testDescribeByGETinRDFXMLConneg(self):
        result = self.__generic(describeQuery, RDFXML, GET, onlyConneg=True)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _RDF_XML], ct
        results = result.convert()
        self.assertEqual(type(results), ConjunctiveGraph)

    # rdf+xml is not a valid alias
    def testDescribeByPOSTinRDFXMLConneg(self):
        result = self.__generic(describeQuery, RDFXML, POST, onlyConneg=True)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _RDF_XML], ct
        results = result.convert()
        self.assertEqual(type(results), ConjunctiveGraph)

    # turtle is not a valid alias (text is the one used)
    def testDescribeByGETinTurtleConneg(self):
        result = self.__generic(describeQuery, TURTLE, GET, onlyConneg=True)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _RDF_N3], ct
        results = result.convert()
        self.assertEqual(type(results), bytes)

    # turtle is not a valid alias (text is the one used)
    def testDescribeByPOSTinTurtleConneg(self):
        result = self.__generic(describeQuery, TURTLE, POST, onlyConneg=True)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _RDF_N3], ct
        results = result.convert()
        self.assertEqual(type(results), bytes)

    @unittest.skip("JSON-LD is not currently supported")
    def testDescribeByGETinJSONLD(self):
        result = self.__generic(describeQuery, JSONLD, GET)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _RDF_JSONLD], ct
        results = result.convert()
        self.assertEqual(type(results), ConjunctiveGraph)

    @unittest.skip("JSON-LD is not currently supported")
    def testDescribeByPOSTinJSONLD(self):
        result = self.__generic(describeQuery, JSONLD, POST)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _RDF_JSONLD], ct
        results = result.convert()
        self.assertEqual(type(results), ConjunctiveGraph)

    # asking for an unexpected return format for DESCRIBE queryType. For a DESCRIBE query type, the default return mimetype (if Accept: */* is sent) is text/turtle
    def testDescribeByGETinCSVConneg(self):
        result = self.__generic(describeQuery, CSV, GET, onlyConneg=True)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _SPARQL_DESCRIBE_CONSTRUCT_POSSIBLE], "returned Content-Type='%s'. Expected fail due to Virtuoso configuration" %(ct)
        results = result.convert()
        self.assertEqual(type(results), ConjunctiveGraph)

    # asking for an unexpected return format for DESCRIBE queryType. For a DESCRIBE query type, the default return mimetype (if Accept: */* is sent) is text/turtle
    def testDescribeByPOSTinCSVConneg(self):
        result = self.__generic(describeQuery, CSV, POST, onlyConneg=True)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _SPARQL_DESCRIBE_CONSTRUCT_POSSIBLE], "returned Content-Type='%s'. Expected fail due to Virtuoso configuration" %(ct)
        results = result.convert()
        self.assertEqual(type(results), ConjunctiveGraph)

    # asking for an unknown return format for DESCRIBE queryType (XML is sent)
    def testDescribeByGETinUnknow(self):
        result = self.__generic(describeQuery, "foo", GET)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _SPARQL_DESCRIBE_CONSTRUCT_POSSIBLE], ct
        results = result.convert()
        self.assertEqual(type(results), ConjunctiveGraph)

    # asking for an unknown return format for DESCRIBE queryType (XML is sent)
    def testDescribeByPOSTinUnknow(self):
        result = self.__generic(describeQuery, "bar", POST)
        ct = result.info()["content-type"]
        assert True in [one in ct for one in _SPARQL_DESCRIBE_CONSTRUCT_POSSIBLE], ct
        results = result.convert()
        self.assertEqual(type(results), ConjunctiveGraph)

################################################################################
################################################################################

    def testQueryBadFormed(self):
        self.assertRaises(QueryBadFormed, self.__generic, queryBadFormed, XML, GET)

    def testQueryManyPrefixes(self):
        result = self.__generic(queryManyPrefixes, XML, GET)

    def testQueryDuplicatedPrefix(self):
        result = self.__generic(queryDuplicatedPrefix, XML, GET)

    def testKeepAlive(self):
        sparql = SPARQLWrapper(endpoint)
        sparql.setQuery('SELECT * WHERE {?s ?p ?o} LIMIT 10')
        sparql.setReturnFormat(JSON)
        sparql.setMethod(GET)
        sparql.setUseKeepAlive()

        sparql.query()
        sparql.query()

    @unittest.skip('Store 4. parser error: Failed to decode SPARQL ID "dbpedia:Victoria\". See #94')
    def testQueryWithComma_1(self):
        result = self.__generic(queryWithCommaInCurie_1, XML, GET)

    @unittest.skip('Store 4. parser error: Failed to decode SPARQL ID "dbpedia:Category\". See #94')
    def testQueryWithComma_2(self):
        result = self.__generic(queryWithCommaInCurie_2, XML, POST)

    def testQueryWithComma_3(self):
        result = self.__generic(queryWithCommaInUri, XML, GET)

if __name__ == "__main__":
    unittest.main()
