from io import BytesIO
from zipfile import ZipFile

from rdflib import Graph, URIRef, Literal, RDF, SKOS, RDFS, DC

from tccm_api.loader.base_loader import BaseLoader
from tccm_api.namespaces import NAMESPACES, HP, SH, NCIT
from tccm_api.utils import curie_to_uri
from urllib.request import urlopen


class NcitFlatLoader(BaseLoader):
    def __init__(self, url):
        resp = urlopen(url)
        self.zipfile = ZipFile(BytesIO(resp.read()))
        self.graph = Graph()
        self.graph.namespace_manager.bind('skos', SKOS)
        self.graph.namespace_manager.bind('sh', SH)
        self.graph.namespace_manager.bind('dc', DC)
        self.graph.namespace_manager.bind('ncit', NCIT)

    def to_tccm_rdf(self, see_also_format =''):
        cs_uri = URIRef("http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl")
        self.graph.add((cs_uri, RDF.type, SKOS.ConceptScheme))
        self.graph.add((cs_uri, DC.description, Literal("A vocabulary for clinical care, translational and basic research, and public information and administrative activities.")))
        self.graph.add((cs_uri, RDFS.seeAlso, Literal("https://ncithesaurus.nci.nih.gov/ncitbrowser/")))
        self.graph.add((cs_uri, SH.namespace, URIRef("http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#")))

        for line in self.zipfile.open("Thesaurus.txt"):
            tokens = line.decode("utf-8").split("\t")
            uri = URIRef(tokens[1][1:-1])
            self.graph.add((uri, RDF.type, SKOS.Concept))
            self.graph.add((uri, SKOS.notation, Literal(tokens[0])))
            self.graph.add((uri, SKOS.definition, Literal(tokens[4])))
            self.graph.add((uri, SKOS.prefLabel, Literal(tokens[3].split("|")[0])))
            if tokens[2]:
                for code in tokens[2].split("|"):
                    code = code.strip()
                    sc_uri = URIRef(curie_to_uri(f"NCIT:{code}", NAMESPACES))
                    self.graph.add((uri, SKOS.broader, sc_uri))
            see_also = f"https://ncit.nci.nih.gov/ncitbrowser/pages/concept_details.jsf?dictionary=NCI%20Thesaurus&code={tokens[0]}"
            self.graph.add((uri, RDFS.seeAlso, Literal(see_also)))
            self.graph.add((uri, SKOS.inScheme, cs_uri))
        with open('ncit-termci.ttl', 'w') as file:
            file.write(self.graph.serialize(format='turtle').decode('utf-8'))


if __name__ == '__main__':
    loader = NcitFlatLoader('https://evs.nci.nih.gov/ftp1/NCI_Thesaurus/Thesaurus.FLAT.zip')
    loader.to_tccm_rdf()
