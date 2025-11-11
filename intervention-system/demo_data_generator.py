"""
Demo Data Generator
Creates realistic synthetic participants with encounters and barrier assessments
"""

from ontology_core import BCIOGraph, INTERVENTION, BCIO
from barrier_assessment import BarrierAssessmentGraph, BarrierAssessment
from datetime import datetime, timedelta
import random
import json


class DemoDataGenerator:
    """Generate realistic synthetic data for system demonstration"""
    
    # Protocol library
    PROTOCOLS = {
        'employment_support_v1': {
            'label': 'Employment Support Protocol v1.0',
            'bcts': [
                {'id': '1.1', 'label': 'Goal setting (behaviour)', 'class': 'bcio:0000001'},
                {'id': '1.4', 'label': 'Action planning', 'class': 'bcio:0000002'},
                {'id': '1.2', 'label': 'Problem solving', 'class': 'bcio:0000003'},
                {'id': '3.1', 'label': 'Social support (practical)', 'class': 'bcio:0000004'},
            ]
        },
        'accommodation_support_v1': {
            'label': 'Accommodation Support Protocol v1.0',
            'bcts': [
                {'id': '12.1', 'label': 'Restructuring physical environment', 'class': 'bcio:0000005'},
                {'id': '3.1', 'label': 'Social support (practical)', 'class': 'bcio:0000004'},
            ]
        }
    }
    
    def __init__(self):
        self.graph = BCIOGraph()
        self.barrier_graph = BarrierAssessmentGraph(self.graph.graph)
        self.participants = []
    
    def generate_participant(self, participant_id: str, 
                           risk_level: str = 'medium',
                           primary_need: str = 'employment') -> dict:
        """Generate a synthetic participant with realistic profile"""
        
        base_date = datetime.now() - timedelta(days=90)
        
        participant_data = {
            'participant_uri': f'http://interventions.org/participant/{participant_id}',
            'participant_id': participant_id,
            'age': random.randint(22, 55),
            'created_date': base_date.isoformat(),
            'tags': self._generate_bcio_tags(risk_level, primary_need)
        }
        
        self.graph.add_participant_instance(participant_data)
        self.participants.append({
            'id': participant_id,
            'risk_level': risk_level,
            'primary_need': primary_need,
            'base_date': base_date
        })
        
        return participant_data
    
    def _generate_bcio_tags(self, risk_level: str, primary_need: str) -> list:
        """Generate appropriate BCIO population tags"""
        tags = [
            {
                'tag_name': 'adult_population',
                'bcio_id': 'BCIO:0000100',
                'tag_category': 'age'
            },
            {
                'tag_name': f'{risk_level}_risk',
                'bcio_id': f'BCIO:000020{ord(risk_level[0])}',
                'tag_category': 'risk'
            },
            {
                'tag_name': f'{primary_need}_need',
                'bcio_id': f'BCIO:000030{ord(primary_need[0])}',
                'tag_category': 'needs'
            }
        ]
        return tags
    
    def generate_barrier_trajectory(self, participant_id: str,
                                   domain: str,
                                   intervention_effective: bool = True) -> list:
        """
        Generate realistic barrier assessment trajectory.
        
        If intervention_effective=True, barriers decrease over time.
        If False, they stay stable or worsen.
        """
        
        # Baseline scores (moderate-to-high barriers)
        baseline_scores = {
            'physical_capability': random.randint(2, 4),
            'psychological_capability': random.randint(5, 8),  # Higher
            'physical_opportunity': random.randint(3, 6),
            'social_opportunity': random.randint(4, 7),
            'reflective_motivation': random.randint(4, 7),
            'automatic_motivation': random.randint(3, 5)
        }
        
        # Add baseline
        participant = next(p for p in self.participants if p['id'] == participant_id)
        base_date = participant['base_date']
        
        self.barrier_graph.add_barrier_assessment(
            participant_id=participant_id,
            domain=domain,
            timepoint='baseline',
            barrier_scores=baseline_scores,
            assessment_date=base_date.isoformat()
        )
        
        trajectory = [{'timepoint': 'baseline', 'scores': baseline_scores.copy()}]
        
        # Generate follow-ups with realistic change patterns
        timepoints = [
            ('day_30', 30, 0.3),    # 30% improvement by day 30
            ('day_90', 90, 0.6),    # 60% improvement by day 90
            ('day_180', 180, 0.8),  # 80% improvement by day 180
        ]
        
        current_scores = baseline_scores.copy()
        
        for timepoint_key, days, improvement_factor in timepoints:
            assessment_date = base_date + timedelta(days=days)
            
            followup_scores = {}
            for barrier_type, baseline_score in baseline_scores.items():
                if intervention_effective:
                    # Realistic improvement with some noise
                    max_possible_improvement = baseline_score * improvement_factor
                    actual_improvement = max_possible_improvement + random.uniform(-1, 0.5)
                    actual_improvement = max(0, actual_improvement)  # Can't go negative
                    
                    new_score = baseline_score - actual_improvement
                    new_score = max(0, min(10, round(new_score)))  # Clamp 0-10
                else:
                    # Non-effective: small random changes
                    change = random.randint(-1, 2)
                    new_score = max(0, min(10, current_scores[barrier_type] + change))
                
                followup_scores[barrier_type] = new_score
            
            self.barrier_graph.add_follow_up_assessment(
                participant_id=participant_id,
                domain=domain,
                timepoint=timepoint_key,
                barrier_scores=followup_scores,
                assessment_date=assessment_date.isoformat()
            )
            
            trajectory.append({
                'timepoint': timepoint_key,
                'scores': followup_scores.copy()
            })
            
            current_scores = followup_scores
        
        return trajectory
    
    def generate_encounter(self, participant_id: str,
                          protocol_id: str,
                          days_after_intake: int,
                          practitioner_id: str = 'CLW001') -> dict:
        """Generate a realistic intervention encounter"""
        
        participant = next(p for p in self.participants if p['id'] == participant_id)
        encounter_date = participant['base_date'] + timedelta(days=days_after_intake)
        
        protocol = self.PROTOCOLS[protocol_id]
        
        # Generate BCT instances with realistic fidelity
        bcts = []
        for i, bct_spec in enumerate(protocol['bcts']):
            # Most are delivered, some partially, rare non-delivery
            fidelity_roll = random.random()
            if fidelity_roll < 0.7:
                fidelity = 'delivered'
            elif fidelity_roll < 0.95:
                fidelity = 'partial'
            else:
                fidelity = 'not_delivered'
            
            bct_data = {
                'bct_instance_uri': f'http://interventions.org/bct/E{encounter_date.strftime("%Y%m%d")}-{participant_id}-{i}',
                'bct_class': bct_spec['class'],
                'bct_id': bct_spec['id'],
                'practitioner_label': bct_spec['label'],
                'formal_label': bct_spec['label'],
                'fidelity': {
                    'value': fidelity,
                    'quality_type': 'bcio:fidelity_quality'
                },
                'notes': f'Delivered as part of {protocol["label"]}',
                'auto_tagged': False
            }
            bcts.append(bct_data)
        
        encounter_data = {
            'encounter_uri': f'http://interventions.org/encounter/E{encounter_date.strftime("%Y%m%d")}-{participant_id}',
            'encounter_id': f'E{encounter_date.strftime("%Y%m%d")}-{participant_id}',
            'timestamp': encounter_date.isoformat(),
            'delivered_to_uri': f'http://interventions.org/participant/{participant_id}',
            'participant_id': participant_id,
            'mode_of_delivery': random.choice(['face_to_face', 'video_call', 'telephone']),
            'duration_minutes': str(random.randint(45, 75)),
            'protocol_id': protocol_id,
            'protocol_label': protocol['label'],
            'practitioner_id': practitioner_id,
            'bcts': bcts,
            'encounter_notes': 'Participant engaged well. Discussed employment goals and barriers.'
        }
        
        self.graph.add_encounter_instance(encounter_data)
        return encounter_data
    
    def generate_complete_case(self, participant_id: str, 
                              scenario: str = 'good_response') -> dict:
        """
        Generate a complete participant case with:
        - Demographics
        - Baseline assessment
        - Multiple encounters
        - Follow-up assessments showing trajectory
        
        Scenarios:
        - 'good_response': Clear improvement over time
        - 'poor_response': Minimal change despite intervention
        - 'delayed_response': Slow start, then improvement
        """
        
        # Create participant
        risk_level = random.choice(['high', 'medium'])
        self.generate_participant(participant_id, risk_level, 'employment')
        
        # Baseline assessment
        self.generate_barrier_trajectory(
            participant_id,
            domain='employment',
            intervention_effective=(scenario != 'poor_response')
        )
        
        # Generate encounters throughout the period
        encounter_dates = [7, 14, 21, 28, 42, 56, 70, 84, 98, 112, 126, 140, 154, 168]
        for days in encounter_dates:
            self.generate_encounter(
                participant_id,
                protocol_id='employment_support_v1',
                days_after_intake=days
            )
        
        return {
            'participant_id': participant_id,
            'scenario': scenario,
            'encounters': len(encounter_dates),
            'assessments': 4  # Baseline + 3 follow-ups
        }
    
    def save(self, filepath: str = 'data/demo_graph.ttl'):
        """Save complete graph to file"""
        from pathlib import Path
        
        # Create directory if it doesn't exist
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        self.graph.save(filepath)
        print(f"[OK] Demo graph saved to {filepath}")
        print(f"   {len(self.participants)} participants")
        print(f"   {self._count_triples()} triples")
    
    def _count_triples(self) -> int:
        """Count total triples in graph"""
        return len(self.graph.graph)
    
    def print_summary(self):
        """Print summary statistics"""
        print("\n" + "="*60)
        print("DEMO DATA SUMMARY")
        print("="*60)
        print(f"\nParticipants: {len(self.participants)}")
        
        for p in self.participants:
            print(f"  • {p['id']} ({p['risk_level']} risk, {p['primary_need']} need)")
        
        # Query encounter count
        query = """
        PREFIX bcio: <http://purl.obolibrary.org/obo/BCIO_>
        SELECT (COUNT(?encounter) as ?count) WHERE {
            ?encounter a bcio:000001 .
        }
        """
        results = list(self.graph.graph.query(query))
        encounter_count = int(results[0][0]) if results else 0
        print(f"\nEncounters: {encounter_count}")
        
        # Query assessment count
        query = """
        PREFIX bcio: <http://purl.obolibrary.org/obo/BCIO_>
        SELECT (COUNT(DISTINCT ?assessment) as ?count) WHERE {
            ?assessment bcio:has_temporal_value ?date .
            ?assessment bcio:assessed_at_timepoint ?tp .
        }
        """
        results = list(self.graph.graph.query(query))
        assessment_count = int(results[0][0]) if results else 0
        print(f"Barrier Assessments: {assessment_count}")
        
        # Query barrier instances
        query = """
        PREFIX bcio: <http://purl.obolibrary.org/obo/BCIO_>
        SELECT (COUNT(?barrier) as ?count) WHERE {
            ?barrier bcio:has_severity_score ?score .
        }
        """
        results = list(self.graph.graph.query(query))
        barrier_count = int(results[0][0]) if results else 0
        print(f"Barrier Instances: {barrier_count}")
        
        print(f"\nTotal Triples: {self._count_triples()}")
        print("="*60 + "\n")


def main():
    """Generate demo dataset with diverse scenarios"""
    
    print("\n>> Generating Demo Data...")
    print("="*60)
    
    generator = DemoDataGenerator()
    
    # Generate participants with different trajectories
    cases = [
        ('P001', 'good_response'),
        ('P002', 'good_response'),
        ('P003', 'poor_response'),
        ('P004', 'good_response'),
        ('P005', 'delayed_response'),
    ]
    
    for participant_id, scenario in cases:
        print(f"\n>> Generating {participant_id} ({scenario})...")
        generator.generate_complete_case(participant_id, scenario)
    
    # Save everything
    generator.save()
    generator.print_summary()
    
    print("\n[OK] Demo data generation complete!")
    print("\nNext steps:")
    print("  1. Run: python barrier_assessment_app.py")
    print("  2. Visit: http://localhost:5001/participant/P001/progress")
    print("  3. Visit: http://localhost:5001/analytics/dashboard")
    print("\n")


if __name__ == '__main__':
    main()
