from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib.namespace import RDF, RDFS, XSD, OWL
from datetime import datetime
import json
from typing import Dict, List, Any

BCIO = Namespace("http://purl.obolibrary.org/obo/BCIO_")
BFO = Namespace("http://purl.obolibrary.org/obo/BFO_")
PATO = Namespace("http://purl.obolibrary.org/obo/PATO_")
IAO = Namespace("http://purl.obolibrary.org/obo/IAO_")
INTERVENTION = Namespace("http://interventions.org/")


class BCIOGraph:
    
    def __init__(self):
        self.graph = Graph()
        self._bind_namespaces()
    
    def _bind_namespaces(self):
        self.graph.bind("bcio", BCIO)
        self.graph.bind("bfo", BFO)
        self.graph.bind("pato", PATO)
        self.graph.bind("iao", IAO)
        self.graph.bind("intervention", INTERVENTION)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("owl", OWL)
        self.graph.bind("xsd", XSD)
    
    def add_encounter_instance(self, encounter_data: Dict[str, Any]) -> URIRef:
        encounter_uri = URIRef(encounter_data['encounter_uri'])
        
        self.graph.add((encounter_uri, RDF.type, BCIO['000001']))
        self.graph.add((encounter_uri, RDF.type, BFO['0000015']))
        
        timestamp_literal = Literal(encounter_data['timestamp'], datatype=XSD.dateTime)
        self.graph.add((encounter_uri, BCIO.has_temporal_value, timestamp_literal))
        
        participant_uri = URIRef(encounter_data['delivered_to_uri'])
        self.graph.add((encounter_uri, BCIO.has_specified_input, participant_uri))
        
        mode_uri = self._create_mode_of_delivery_quality(
            encounter_uri, 
            encounter_data['mode_of_delivery']
        )
        
        duration_uri = self._create_duration_quality(
            encounter_uri,
            encounter_data['duration_minutes']
        )
        
        protocol_uri = INTERVENTION[f"protocol/{encounter_data['protocol_id']}"]
        self.graph.add((encounter_uri, BFO['0000055'], protocol_uri))
        
        practitioner_uri = INTERVENTION[f"practitioner/{encounter_data['practitioner_id']}"]
        self.graph.add((encounter_uri, BCIO.has_specified_agent, practitioner_uri))
        
        for bct_data in encounter_data.get('bcts', []):
            bct_uri = self.add_bct_instance(bct_data, encounter_uri)
            self.graph.add((encounter_uri, BFO['0000051'], bct_uri))
        
        if encounter_data.get('encounter_notes'):
            notes_literal = Literal(encounter_data['encounter_notes'], lang='en')
            self.graph.add((encounter_uri, RDFS.comment, notes_literal))
        
        return encounter_uri
    
    def add_bct_instance(self, bct_data: Dict[str, Any], 
                         encounter_uri: URIRef) -> URIRef:
        bct_uri = URIRef(bct_data['bct_instance_uri'])
        
        bct_class_uri = self._parse_bcio_uri(bct_data['bct_class'])
        self.graph.add((bct_uri, RDF.type, bct_class_uri))
        
        fidelity_uri = self._create_fidelity_quality(
            bct_uri,
            bct_data['fidelity']
        )
        
        practitioner_label = Literal(bct_data['practitioner_label'], lang='en')
        self.graph.add((bct_uri, RDFS.label, practitioner_label))
        
        formal_label = Literal(bct_data['formal_label'], lang='en')
        self.graph.add((bct_uri, IAO['0000118'], formal_label))
        
        if bct_data.get('notes'):
            notes_literal = Literal(bct_data['notes'], lang='en')
            self.graph.add((bct_uri, RDFS.comment, notes_literal))
        
        auto_tagged = Literal(bct_data.get('auto_tagged', False), 
                            datatype=XSD.boolean)
        self.graph.add((bct_uri, BCIO.auto_tagged, auto_tagged))
        
        self.graph.add((bct_uri, BFO['0000050'], encounter_uri))
        
        return bct_uri
    
    def _create_fidelity_quality(self, bct_uri: URIRef, 
                                 fidelity_data: Dict[str, str]) -> URIRef:
        fidelity_uri = URIRef(f"{bct_uri}/fidelity_quality")
        
        self.graph.add((fidelity_uri, RDF.type, PATO['0000001']))
        self.graph.add((fidelity_uri, RDF.type, BCIO.fidelity_quality))
        
        self.graph.add((fidelity_uri, BFO['0000052'], bct_uri))
        
        fidelity_value = fidelity_data['value']
        value_literal = Literal(fidelity_value, datatype=XSD.string)
        self.graph.add((fidelity_uri, BCIO.has_quality_value, value_literal))
        
        quality_type_uri = self._parse_bcio_uri(fidelity_data['quality_type'])
        self.graph.add((fidelity_uri, RDF.type, quality_type_uri))
        
        return fidelity_uri
    
    def _create_mode_of_delivery_quality(self, encounter_uri: URIRef, 
                                        mode: str) -> URIRef:
        mode_uri = URIRef(f"{encounter_uri}/mode_quality")
        
        self.graph.add((mode_uri, RDF.type, BCIO.mode_of_delivery))
        self.graph.add((mode_uri, BFO['0000052'], encounter_uri))
        
        mode_literal = Literal(mode, datatype=XSD.string)
        self.graph.add((mode_uri, BCIO.has_quality_value, mode_literal))
        
        return mode_uri
    
    def _create_duration_quality(self, encounter_uri: URIRef, 
                                duration_minutes: str) -> URIRef:
        duration_uri = URIRef(f"{encounter_uri}/duration_quality")
        
        self.graph.add((duration_uri, RDF.type, PATO['0001309']))
        self.graph.add((duration_uri, BFO['0000052'], encounter_uri))
        
        duration_literal = Literal(int(duration_minutes), datatype=XSD.integer)
        self.graph.add((duration_uri, IAO['0000004'], duration_literal))
        
        self.graph.add((duration_uri, IAO['0000039'], BCIO.minutes))
        
        return duration_uri
    
    def add_participant_instance(self, participant_data: Dict[str, Any]) -> URIRef:
        participant_uri = URIRef(participant_data['participant_uri'])
        
        self.graph.add((participant_uri, RDF.type, BFO['0000040']))
        self.graph.add((participant_uri, RDF.type, BCIO.intervention_recipient))
        
        participant_id = Literal(participant_data['participant_id'], datatype=XSD.string)
        self.graph.add((participant_uri, IAO['0000578'], participant_id))
        
        age_uri = self._create_age_attribute(participant_uri, participant_data['age'])
        
        for tag_data in participant_data.get('tags', []):
            attribute_uri = self._create_population_attribute(
                participant_uri,
                tag_data
            )
        
        created_literal = Literal(participant_data['created_date'], datatype=XSD.dateTime)
        self.graph.add((participant_uri, IAO['0000579'], created_literal))
        
        return participant_uri
    
    def _create_age_attribute(self, participant_uri: URIRef, age: int) -> URIRef:
        age_uri = URIRef(f"{participant_uri}/age_attribute")
        
        self.graph.add((age_uri, RDF.type, PATO['0000011']))
        self.graph.add((age_uri, BFO['0000052'], participant_uri))
        
        age_literal = Literal(age, datatype=XSD.integer)
        self.graph.add((age_uri, IAO['0000004'], age_literal))
        
        self.graph.add((age_uri, IAO['0000039'], BCIO.years))
        
        return age_uri
    
    def _create_population_attribute(self, participant_uri: URIRef, 
                                    tag_data: Dict[str, str]) -> URIRef:
        attribute_uri = URIRef(f"{participant_uri}/attribute/{tag_data['tag_name']}")
        
        bcio_class_uri = self._parse_bcio_uri_from_id(tag_data.get('bcio_id', ''))
        
        self.graph.add((attribute_uri, RDF.type, bcio_class_uri))
        self.graph.add((attribute_uri, RDF.type, BFO['0000020']))
        
        self.graph.add((attribute_uri, BFO['0000052'], participant_uri))
        
        label = Literal(tag_data['tag_name'].replace('_', ' '), lang='en')
        self.graph.add((attribute_uri, RDFS.label, label))
        
        category = Literal(tag_data['tag_category'], datatype=XSD.string)
        self.graph.add((attribute_uri, BCIO.attribute_category, category))
        
        return attribute_uri
    
    def _parse_bcio_uri(self, prefixed_uri: str) -> URIRef:
        if prefixed_uri.startswith('bcio:'):
            local_part = prefixed_uri.replace('bcio:', '')
            return BCIO[local_part]
        return URIRef(prefixed_uri)
    
    def _parse_bcio_uri_from_id(self, bcio_id: str) -> URIRef:
        if not bcio_id:
            return BCIO['unknown']
        
        if bcio_id.startswith('BCIO:'):
            local_part = bcio_id.replace('BCIO:', '').replace('_', '')
            if local_part.isdigit():
                local_part = local_part.zfill(7)
            return BCIO[local_part]
        elif bcio_id.startswith('bcio:'):
            return self._parse_bcio_uri(bcio_id)
        else:
            return BCIO[bcio_id.replace(':', '_')]
    
    def serialize(self, format='turtle') -> str:
        return self.graph.serialize(format=format)
    
    def save(self, filepath: str, format='turtle'):
        self.graph.serialize(destination=filepath, format=format)
    
    def query(self, sparql_query: str):
        return self.graph.query(sparql_query)


class JSONLDConverter:
    
    @staticmethod
    def add_context(data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        
        if data_type == 'encounter':
            context = {
                "@vocab": "http://purl.obolibrary.org/obo/BCIO_",
                "bcio": "http://purl.obolibrary.org/obo/BCIO_",
                "bfo": "http://purl.obolibrary.org/obo/BFO_",
                "pato": "http://purl.obolibrary.org/obo/PATO_",
                "encounter_uri": "@id",
                "bct_instance_uri": "@id",
                "delivered_to_uri": {"@id": "bcio:has_specified_input", "@type": "@id"},
                "timestamp": {"@type": "xsd:dateTime"}
            }
        elif data_type == 'participant':
            context = {
                "@vocab": "http://purl.obolibrary.org/obo/BCIO_",
                "bcio": "http://purl.obolibrary.org/obo/BCIO_",
                "bfo": "http://purl.obolibrary.org/obo/BFO_",
                "participant_uri": "@id",
                "age": {"@type": "xsd:integer"},
                "created_date": {"@type": "xsd:dateTime"}
            }
        else:
            context = {"@vocab": "http://purl.obolibrary.org/obo/BCIO_"}
        
        return {
            "@context": context,
            **data
        }


class TripleStoreManager:
    
    def __init__(self, endpoint_url: str = None):
        self.endpoint_url = endpoint_url or "http://localhost:3030/bcio-data"
        self.query_endpoint = f"{self.endpoint_url}/query"
        self.update_endpoint = f"{self.endpoint_url}/update"
    
    def upload_graph(self, graph: Graph):
        from rdflib.plugins.stores import sparqlstore
        
        try:
            store = sparqlstore.SPARQLUpdateStore()
            store.open((self.query_endpoint, self.update_endpoint))
            
            for triple in graph:
                store.add(triple)
            
            store.close()
            return True
        except Exception as e:
            print(f"Triple store upload failed: {e}")
            return False
    
    def query(self, sparql_query: str):
        from rdflib.plugins.stores import sparqlstore
        
        try:
            store = sparqlstore.SPARQLStore()
            store.open(self.query_endpoint)
            
            results = store.query(sparql_query)
            store.close()
            
            return results
        except Exception as e:
            print(f"SPARQL query failed: {e}")
            return None


def validate_against_bcio(graph: Graph, bcio_ontology_path: str = None) -> Dict[str, Any]:
    
    validation_results = {
        'valid': True,
        'warnings': [],
        'errors': []
    }
    
    query = """
    PREFIX bcio: <http://purl.obolibrary.org/obo/BCIO_>
    SELECT ?encounter WHERE {
        ?encounter a bcio:000001 .
        FILTER NOT EXISTS { ?encounter bcio:has_specified_input ?participant }
    }
    """
    
    results = graph.query(query)
    if len(results) > 0:
        validation_results['warnings'].append(
            "Some encounters missing participant references"
        )
    
    return validation_results
