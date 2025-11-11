"""
COM-B Barrier Assessment Module
Extends ontology_core.py with barrier assessment capabilities
"""

from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD
from datetime import datetime
from typing import Dict, List, Any, Optional
from ontology_core import BCIO, BFO, PATO, IAO, INTERVENTION


# COM-B Barrier Classes (Custom Extensions to BCIO)
BARRIER = Namespace("http://interventions.org/barrier/")


class BarrierAssessment:
    """
    Represents a COM-B barrier assessment at a specific timepoint.
    
    Maps to the 6 COM-B categories:
    - Physical Capability
    - Psychological Capability  
    - Physical Opportunity
    - Social Opportunity
    - Reflective Motivation
    - Automatic Motivation
    """
    
    BARRIER_TYPES = {
        'physical_capability': {
            'class': 'Physical_Capability_Barrier',
            'label': 'Physical Capability Barrier',
            'mechanism': 'BCIO_0000532'  # Skills mechanism
        },
        'psychological_capability': {
            'class': 'Psychological_Capability_Barrier', 
            'label': 'Psychological Capability Barrier',
            'mechanism': 'BCIO_0000532'  # Skills mechanism
        },
        'physical_opportunity': {
            'class': 'Physical_Opportunity_Barrier',
            'label': 'Physical Opportunity Barrier',
            'mechanism': 'BCIO_0000536'  # Environmental context mechanism
        },
        'social_opportunity': {
            'class': 'Social_Opportunity_Barrier',
            'label': 'Social Opportunity Barrier', 
            'mechanism': 'BCIO_0000537'  # Social influences mechanism
        },
        'reflective_motivation': {
            'class': 'Reflective_Motivation_Barrier',
            'label': 'Reflective Motivation Barrier',
            'mechanism': 'BCIO_0000533'  # Beliefs mechanism
        },
        'automatic_motivation': {
            'class': 'Automatic_Motivation_Barrier',
            'label': 'Automatic Motivation Barrier',
            'mechanism': 'BCIO_0000534'  # Emotion mechanism
        }
    }
    
    TIMEPOINTS = {
        'baseline': 'timepoint:Baseline',
        'day_30': 'timepoint:Day_30',
        'day_90': 'timepoint:Day_90', 
        'day_180': 'timepoint:Day_180'
    }
    
    DOMAINS = {
        'employment': 'Employment_Domain',
        'accommodation': 'Accommodation_Domain',
        'substance_use': 'Substance_Use_Domain',
        'relationships': 'Relationships_Domain',
        'attitudes': 'Attitudes_Domain',
        'leisure': 'Leisure_Domain'
    }


class BarrierAssessmentGraph:
    """Extends BCIOGraph with barrier assessment capabilities"""
    
    def __init__(self, base_graph: Graph = None):
        self.graph = base_graph if base_graph else Graph()
        self._bind_namespaces()
    
    def _bind_namespaces(self):
        self.graph.bind("barrier", BARRIER)
        self.graph.bind("bcio", BCIO)
        self.graph.bind("bfo", BFO)
        self.graph.bind("intervention", INTERVENTION)
    
    def add_barrier_assessment(self, 
                              participant_id: str,
                              domain: str,
                              timepoint: str,
                              barrier_scores: Dict[str, int],
                              assessment_date: str = None) -> URIRef:
        """
        Add a complete barrier assessment for a participant.
        
        Args:
            participant_id: Participant identifier
            domain: Criminogenic need domain (employment, accommodation, etc.)
            timepoint: Assessment timepoint (baseline, day_30, day_90, day_180)
            barrier_scores: Dict mapping barrier type to severity score (0-10)
            assessment_date: ISO date string, defaults to now
            
        Returns:
            URIRef of the assessment event
        """
        
        if assessment_date is None:
            assessment_date = datetime.now().isoformat()
        
        # Create assessment event URI
        assessment_uri = INTERVENTION[
            f"assessment/{participant_id}/{domain}/{timepoint}/{assessment_date}"
        ]
        
        # Type as assessment event
        self.graph.add((assessment_uri, RDF.type, BCIO['0000001']))  # process
        self.graph.add((assessment_uri, RDFS.label, 
                       Literal(f"Barrier Assessment - {domain}", lang='en')))
        
        # Link to participant
        participant_uri = INTERVENTION[f"participant/{participant_id}"]
        self.graph.add((assessment_uri, BCIO.has_specified_input, participant_uri))
        
        # Temporal properties
        self.graph.add((assessment_uri, BCIO.has_temporal_value, 
                       Literal(assessment_date, datatype=XSD.dateTime)))
        timepoint_uri = INTERVENTION[BarrierAssessment.TIMEPOINTS[timepoint]]
        self.graph.add((assessment_uri, BCIO.assessed_at_timepoint, timepoint_uri))
        
        # Domain 
        domain_uri = INTERVENTION[f"domain/{BarrierAssessment.DOMAINS[domain]}"]
        self.graph.add((assessment_uri, BCIO.concerns_domain, domain_uri))
        
        # Create barrier instances for each COM-B category
        for barrier_type, score in barrier_scores.items():
            barrier_uri = self._create_barrier_instance(
                assessment_uri,
                participant_uri, 
                barrier_type,
                score,
                domain,
                timepoint,
                assessment_date
            )
            self.graph.add((assessment_uri, BFO['0000051'], barrier_uri))
        
        return assessment_uri
    
    def _create_barrier_instance(self,
                                assessment_uri: URIRef,
                                participant_uri: URIRef,
                                barrier_type: str,
                                severity_score: int,
                                domain: str,
                                timepoint: str,
                                assessment_date: str) -> URIRef:
        """Create an individual barrier instance"""
        
        barrier_info = BarrierAssessment.BARRIER_TYPES[barrier_type]
        
        # Create unique URI for this barrier instance
        barrier_uri = BARRIER[
            f"{participant_uri.split('/')[-1]}/{domain}/{barrier_type}/{timepoint}"
        ]
        
        # Type as specific barrier class
        barrier_class = BARRIER[barrier_info['class']]
        self.graph.add((barrier_uri, RDF.type, barrier_class))
        self.graph.add((barrier_uri, RDF.type, BFO['0000020']))  # quality
        
        # Label
        self.graph.add((barrier_uri, RDFS.label, 
                       Literal(barrier_info['label'], lang='en')))
        
        # Inheres in participant
        self.graph.add((barrier_uri, BFO['0000052'], participant_uri))
        
        # Domain
        domain_uri = INTERVENTION[f"domain/{BarrierAssessment.DOMAINS[domain]}"]
        self.graph.add((barrier_uri, BCIO.concerns_domain, domain_uri))
        
        # Timepoint
        timepoint_uri = INTERVENTION[BarrierAssessment.TIMEPOINTS[timepoint]]
        self.graph.add((barrier_uri, BCIO.assessed_at_timepoint, timepoint_uri))
        
        # Severity score (0-10)
        self.graph.add((barrier_uri, BCIO.has_severity_score, 
                       Literal(severity_score, datatype=XSD.integer)))
        
        # Assessment date
        self.graph.add((barrier_uri, BCIO.has_assessment_date,
                       Literal(assessment_date, datatype=XSD.dateTime)))
        
        # Link to mechanism this barrier type is addressable by
        mechanism_uri = BCIO[barrier_info['mechanism']]
        self.graph.add((barrier_uri, BCIO.addressable_by_mechanism, mechanism_uri))
        
        return barrier_uri
    
    def add_follow_up_assessment(self,
                                 participant_id: str,
                                 domain: str,
                                 timepoint: str,
                                 barrier_scores: Dict[str, int],
                                 assessment_date: str = None) -> URIRef:
        """
        Add a follow-up assessment and automatically calculate change scores.
        Links to baseline through is_reassessment_of property.
        """
        
        # Create the follow-up assessment
        followup_uri = self.add_barrier_assessment(
            participant_id, domain, timepoint, barrier_scores, assessment_date
        )
        
        # Query for baseline barriers to link
        domain_uri = f"<http://interventions.org/domain/{BarrierAssessment.DOMAINS[domain]}>"
        baseline_query = f"""
        PREFIX barrier: <http://interventions.org/barrier/>
        PREFIX bcio: <http://purl.obolibrary.org/obo/BCIO_>
        PREFIX intervention: <http://interventions.org/>
        
        SELECT ?barrier ?barrier_type WHERE {{
            ?barrier bcio:concerns_domain {domain_uri} .
            ?barrier bcio:assessed_at_timepoint <http://interventions.org/timepoint:Baseline> .
            ?barrier bcio:has_severity_score ?score .
            FILTER(STRSTARTS(STR(?barrier), STR(barrier:)))
        }}
        """
        
        baseline_results = self.graph.query(baseline_query)
        
        # Link follow-up barriers to baseline barriers
        for barrier_type, followup_score in barrier_scores.items():
            followup_barrier_uri = BARRIER[
                f"{participant_id}/{domain}/{barrier_type}/{timepoint}"
            ]
            baseline_barrier_uri = BARRIER[
                f"{participant_id}/{domain}/{barrier_type}/baseline"
            ]
            
            # Create reassessment relationship
            self.graph.add((followup_barrier_uri, BCIO.is_reassessment_of, 
                           baseline_barrier_uri))
            
            # Calculate and store change score
            baseline_score = self._get_barrier_score(baseline_barrier_uri)
            if baseline_score is not None:
                change_score = followup_score - baseline_score
                self.graph.add((followup_barrier_uri, BCIO.has_change_from_baseline,
                               Literal(change_score, datatype=XSD.integer)))
                
                # Classify outcome
                if change_score < 0:
                    self.graph.add((followup_barrier_uri, RDF.type, 
                                   BARRIER.Barrier_Reduction))
                elif change_score > 0:
                    self.graph.add((followup_barrier_uri, RDF.type,
                                   BARRIER.Barrier_Increase))
                else:
                    self.graph.add((followup_barrier_uri, RDF.type,
                                   BARRIER.Barrier_Stable))
        
        return followup_uri
    
    def _get_barrier_score(self, barrier_uri: URIRef) -> Optional[int]:
        """Get severity score for a barrier instance"""
        query = f"""
        PREFIX bcio: <http://purl.obolibrary.org/obo/BCIO_>
        SELECT ?score WHERE {{
            <{barrier_uri}> bcio:has_severity_score ?score .
        }}
        """
        results = list(self.graph.query(query))
        if results:
            return int(results[0][0])
        return None
    
    def get_participant_barriers(self, 
                                participant_id: str,
                                domain: str = None,
                                timepoint: str = None) -> List[Dict]:
        """
        Query barrier assessments for a participant.
        
        Returns list of dicts with barrier details.
        """
        
        domain_filter = ""
        if domain:
            domain_uri = f"<http://interventions.org/domain/{BarrierAssessment.DOMAINS[domain]}>"
            domain_filter = f"?barrier bcio:concerns_domain {domain_uri} ."
        
        timepoint_filter = ""
        if timepoint:
            timepoint_uri = f"<http://interventions.org/{BarrierAssessment.TIMEPOINTS[timepoint]}>"
            timepoint_filter = f"?barrier bcio:assessed_at_timepoint {timepoint_uri} ."
        
        query = f"""
        PREFIX barrier: <http://interventions.org/barrier/>
        PREFIX bcio: <http://purl.obolibrary.org/obo/BCIO_>
        PREFIX intervention: <http://interventions.org/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT ?barrier ?label ?domain ?timepoint ?score ?change WHERE {{
            ?barrier bcio:has_severity_score ?score .
            ?barrier rdfs:label ?label .
            ?barrier bcio:concerns_domain ?domain .
            ?barrier bcio:assessed_at_timepoint ?timepoint .
            OPTIONAL {{ ?barrier bcio:has_change_from_baseline ?change }}
            {domain_filter}
            {timepoint_filter}
            FILTER(CONTAINS(STR(?barrier), "{participant_id}"))
        }}
        ORDER BY ?domain ?timepoint
        """
        
        results = []
        for row in self.graph.query(query):
            results.append({
                'barrier_uri': str(row.barrier),
                'label': str(row.label),
                'domain': str(row.domain).split('/')[-1],
                'timepoint': str(row.timepoint).split(':')[-1],
                'severity_score': int(row.score),
                'change_from_baseline': int(row.change) if row.change else None
            })
        
        return results


# Employment Domain Barrier Questions
EMPLOYMENT_BARRIERS = {
    'physical_capability': {
        'question': 'Does the participant have physical limitations preventing work?',
        'examples': 'Chronic pain, physical injury, mobility issues',
        'scale': '0 (No barriers) - 10 (Severe barriers preventing any work)'
    },
    'psychological_capability': {
        'question': 'Does the participant lack job search skills or work-related knowledge?',
        'examples': 'No CV, doesn\'t know how to interview, lacks work skills',
        'scale': '0 (Fully capable) - 10 (Major skill deficits)'
    },
    'physical_opportunity': {
        'question': 'Does the participant lack physical access to employment?',
        'examples': 'No transport, no computer/phone, no suitable jobs in area',
        'scale': '0 (Full access) - 10 (No physical access)'
    },
    'social_opportunity': {
        'question': 'Does the participant lack social connections for employment?',
        'examples': 'No references, criminal record stigma, social isolation',
        'scale': '0 (Strong network) - 10 (Completely isolated)'
    },
    'reflective_motivation': {
        'question': 'Does the participant lack belief they can get/keep work?',
        'examples': 'Low self-efficacy, doesn\'t believe employers will hire them',
        'scale': '0 (Highly confident) - 10 (No belief in ability)'
    },
    'automatic_motivation': {
        'question': 'Does the participant lack drive or feel anxious about work?',
        'examples': 'Depression, anxiety about failure, low energy',
        'scale': '0 (Strong drive) - 10 (Severe emotional barriers)'
    }
}
