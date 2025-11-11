"""
Unified Intervention Tracking System
Combines participant intake, encounter recording, barrier assessment, and analytics
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from pathlib import Path
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ontology_core import BCIOGraph
from barrier_assessment import BarrierAssessmentGraph, BarrierAssessment, EMPLOYMENT_BARRIERS
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'

# Storage
DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)
GRAPH_FILE = DATA_DIR / 'demo_graph.ttl'


def load_graph():
    """Load existing graph or create new one"""
    graph = BarrierAssessmentGraph()
    bcio_graph = BCIOGraph()
    graph.graph = bcio_graph.graph
    
    if GRAPH_FILE.exists():
        try:
            graph.graph.parse(GRAPH_FILE, format='turtle')
        except:
            pass
    return graph


def save_graph(graph):
    """Persist graph to disk"""
    graph.graph.serialize(destination=str(GRAPH_FILE), format='turtle')


# ============================================================================
# HOME & NAVIGATION
# ============================================================================

@app.route('/')
def index():
    """Main dashboard/home page"""
    return render_template('index.html')


# ============================================================================
# PARTICIPANT MANAGEMENT
# ============================================================================

@app.route('/participants')
def participants_list():
    """View all participants"""
    graph = load_graph()
    
    # Query all participants
    query = """
    PREFIX intervention: <http://interventions.org/>
    PREFIX bfo: <http://purl.obolibrary.org/obo/BFO_>
    PREFIX iao: <http://purl.obolibrary.org/obo/IAO_>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?participant ?participant_id ?age ?created WHERE {
        ?participant a bfo:0000040 .
        ?participant iao:0000578 ?participant_id .
        OPTIONAL { ?participant iao:0000579 ?created }
    }
    """
    
    participants = []
    results = graph.graph.query(query)
    for row in results:
        participants.append({
            'participant_uri': str(row.participant),
            'participant_id': str(row.participant_id),
            'created_date': str(row.created) if row.created else '',
            'age': 0,  # Would extract from graph
            'tags': [],  # Would extract from graph
            'gender': 'unknown',
            'days_since_release': 0,
            'supervision_status': 'unknown',
            'housing_status': 'unknown',
            'housing_type': None,
            'substances': [],
            'mental_health': [],
            'disability_status': None,
            'disability_duration': None,
            'education_level': None,
            'relationship_status': None,
            'employment_status': None
        })
    
    return render_template('view_participants.html', participants=participants)


@app.route('/participant/new', methods=['GET', 'POST'])
def new_participant():
    """Create new participant"""
    if request.method == 'POST':
        # Generate participant ID
        graph = load_graph()
        
        # Count existing participants
        query = """
        PREFIX bfo: <http://purl.obolibrary.org/obo/BFO_>
        SELECT (COUNT(?p) as ?count) WHERE {
            ?p a bfo:0000040 .
        }
        """
        results = list(graph.graph.query(query))
        count = int(results[0][0]) if results else 0
        
        participant_id = f"P{str(count + 1).zfill(3)}"
        
        participant_data = {
            'participant_uri': f'http://interventions.org/participant/{participant_id}',
            'participant_id': participant_id,
            'age': int(request.form.get('age', 25)),
            'created_date': datetime.now().isoformat(),
            'tags': []
        }
        
        # Add to graph using BCIOGraph
        bcio_graph = BCIOGraph()
        bcio_graph.graph = graph.graph
        bcio_graph.add_participant_instance(participant_data)
        save_graph(graph)
        
        flash(f'Participant {participant_id} created successfully!', 'success')
        return redirect(url_for('participants_list'))
    
    # Pass empty definitions dict for template
    definitions = {}
    return render_template('intake_form.html', definitions=definitions)


@app.route('/submit', methods=['POST'])
def submit_participant():
    """Handle JSON submission from intake form"""
    try:
        data = request.get_json()
        
        # Generate participant ID
        graph = load_graph()
        
        # Count existing participants
        query = """
        PREFIX bfo: <http://purl.obolibrary.org/obo/BFO_>
        SELECT (COUNT(?p) as ?count) WHERE {
            ?p a bfo:0000040 .
        }
        """
        results = list(graph.graph.query(query))
        count = int(results[0][0]) if results else 0
        
        participant_id = f"P{str(count + 1).zfill(3)}"
        
        # Build participant data
        participant_data = {
            'participant_uri': f'http://interventions.org/participant/{participant_id}',
            'participant_id': participant_id,
            'age': int(data.get('age', 25)),
            'created_date': datetime.now().isoformat(),
            'tags': []
        }
        
        # Add basic BCIO tags based on form data
        bcio_tags = []
        
        # Add to graph
        bcio_graph = BCIOGraph()
        bcio_graph.graph = graph.graph
        bcio_graph.add_participant_instance(participant_data)
        save_graph(graph)
        
        # Return JSON response
        return jsonify({
            'success': True,
            'participant_id': participant_id,
            'tag_count': len(bcio_tags),
            'bcio_tags': bcio_tags,
            'participant_uri': participant_data['participant_uri']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/participant/<participant_id>/encounters')
def participant_encounters(participant_id):
    """View all encounters for a specific participant"""
    graph = load_graph()
    
    # Query encounters for this participant
    query = f"""
    PREFIX bcio: <http://purl.obolibrary.org/obo/BCIO_>
    PREFIX bfo: <http://purl.obolibrary.org/obo/BFO_>
    PREFIX intervention: <http://interventions.org/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?encounter ?timestamp ?protocol ?practitioner WHERE {{
        ?encounter a bcio:000001 .
        ?encounter bcio:has_specified_input <http://interventions.org/participant/{participant_id}> .
        ?encounter bcio:has_temporal_value ?timestamp .
        OPTIONAL {{ ?encounter bfo:0000055 ?protocol }}
        OPTIONAL {{ ?encounter bcio:has_specified_agent ?practitioner }}
    }}
    ORDER BY DESC(?timestamp)
    """
    
    encounters = []
    for row in graph.graph.query(query):
        encounters.append({
            'encounter_id': str(row.encounter).split('/')[-1],
            'timestamp': str(row.timestamp),
            'protocol_label': str(row.protocol).split('/')[-1] if row.protocol else 'Unknown',
            'practitioner_id': str(row.practitioner).split('/')[-1] if row.practitioner else 'Unknown',
            'duration_minutes': '60',
            'mode_of_delivery': 'face_to_face',
            'bcts': [],
            'encounter_notes': ''
        })
    
    return render_template('participant_encounters.html', 
                         participant_id=participant_id,
                         encounters=encounters)


# ============================================================================
# ENCOUNTER RECORDING
# ============================================================================

@app.route('/encounters')
def encounters_list():
    """View all encounters"""
    graph = load_graph()
    
    # Query all encounters
    query = """
    PREFIX bcio: <http://purl.obolibrary.org/obo/BCIO_>
    PREFIX bfo: <http://purl.obolibrary.org/obo/BFO_>
    PREFIX intervention: <http://interventions.org/>
    
    SELECT ?encounter ?timestamp ?participant WHERE {
        ?encounter a bcio:000001 .
        ?encounter bcio:has_temporal_value ?timestamp .
        ?encounter bcio:has_specified_input ?participant .
    }
    ORDER BY DESC(?timestamp)
    """
    
    encounters = []
    for row in graph.graph.query(query):
        participant_id = str(row.participant).split('/')[-1]
        encounters.append({
            'encounter_id': str(row.encounter).split('/')[-1],
            'participant_id': participant_id,
            'timestamp': str(row.timestamp),
            'protocol_label': 'Employment Support Protocol',
            'practitioner_id': 'CLW001',
            'duration_minutes': '60',
            'mode_of_delivery': 'face_to_face',
            'bcts': [],
            'num_bcts': 0,
            'encounter_notes': ''
        })
    
    return render_template('view_encounters.html', encounters=encounters)


@app.route('/encounter/new', methods=['GET', 'POST'])
def new_encounter():
    """Record new encounter"""
    if request.method == 'POST':
        graph = load_graph()
        bcio_graph = BCIOGraph()
        bcio_graph.graph = graph.graph
        
        participant_id = request.form.get('participant_id')
        
        encounter_data = {
            'encounter_uri': f'http://interventions.org/encounter/E{datetime.now().strftime("%Y%m%d%H%M%S")}-{participant_id}',
            'encounter_id': f'E{datetime.now().strftime("%Y%m%d%H%M%S")}-{participant_id}',
            'timestamp': datetime.now().isoformat(),
            'delivered_to_uri': f'http://interventions.org/participant/{participant_id}',
            'participant_id': participant_id,
            'mode_of_delivery': request.form.get('mode_of_delivery', 'face_to_face'),
            'duration_minutes': request.form.get('duration_minutes', '60'),
            'protocol_id': request.form.get('protocol_id', 'employment_support_v1'),
            'protocol_label': 'Employment Support Protocol v1.0',
            'practitioner_id': request.form.get('practitioner_id', 'CLW001'),
            'bcts': [],
            'encounter_notes': request.form.get('notes', '')
        }
        
        bcio_graph.add_encounter_instance(encounter_data)
        save_graph(graph)
        
        flash('Encounter recorded successfully!', 'success')
        return redirect(url_for('encounters_list'))
    
    # Get participants for dropdown
    graph = load_graph()
    query = """
    PREFIX iao: <http://purl.obolibrary.org/obo/IAO_>
    PREFIX bfo: <http://purl.obolibrary.org/obo/BFO_>
    SELECT ?participant_id WHERE {
        ?p a bfo:0000040 .
        ?p iao:0000578 ?participant_id .
    }
    """
    
    participants = []
    for row in graph.graph.query(query):
        participants.append({
            'id': str(row.participant_id),
            'name': f'Participant {str(row.participant_id)}'
        })
    
    # Define protocols for dropdown with their BCTs
    protocols = {
        'employment_support_v1': {
            'label': 'Employment Support Protocol v1.0',
            'description': 'Standard employment support intervention',
            'bcts': [
                {'bct_id': '1.1', 'label': 'Goal setting (behaviour)', 'class': 'bcio:0000001'},
                {'bct_id': '1.4', 'label': 'Action planning', 'class': 'bcio:0000002'},
                {'bct_id': '1.2', 'label': 'Problem solving', 'class': 'bcio:0000003'},
                {'bct_id': '3.1', 'label': 'Social support (practical)', 'class': 'bcio:0000004'},
                {'bct_id': '2.3', 'label': 'Self-monitoring of behaviour', 'class': 'bcio:0000005'},
                {'bct_id': '15.1', 'label': 'Verbal persuasion about capability', 'class': 'bcio:0000006'},
            ]
        },
        'accommodation_support_v1': {
            'label': 'Accommodation Support Protocol v1.0',
            'description': 'Housing and accommodation support',
            'bcts': [
                {'bct_id': '12.1', 'label': 'Restructuring physical environment', 'class': 'bcio:0000007'},
                {'bct_id': '3.1', 'label': 'Social support (practical)', 'class': 'bcio:0000004'},
                {'bct_id': '1.4', 'label': 'Action planning', 'class': 'bcio:0000002'},
                {'bct_id': '4.1', 'label': 'Instruction on how to perform behaviour', 'class': 'bcio:0000008'},
            ]
        }
    }
    
    # Define referral catalog for the referral section
    referral_catalog = {
        'employment': {
            'label': 'Employment Services',
            'services': ['Job Centre Plus', 'Work Programme', 'Restart Scheme']
        },
        'accommodation': {
            'label': 'Housing Services',
            'services': ['Local Housing Authority', 'Shelter', 'Crisis']
        },
        'substance_use': {
            'label': 'Substance Use Services',
            'services': ['Local Drug & Alcohol Service', 'AA/NA', 'SMART Recovery']
        },
        'mental_health': {
            'label': 'Mental Health Services',
            'services': ['IAPT', 'Community Mental Health Team', 'Crisis Team']
        }
    }
    
    return render_template('encounter_form.html', 
                         participants=participants, 
                         protocols=protocols,
                         referral_catalog=referral_catalog)


@app.route('/encounter/submit', methods=['POST'])
def submit_encounter():
    """Handle encounter form submission with BCT fidelity tracking"""
    graph = load_graph()
    bcio_graph = BCIOGraph()
    bcio_graph.graph = graph.graph
    
    participant_id = request.form.get('participant_id')
    protocol_id = request.form.get('protocol_id', 'employment_support_v1')
    
    # Get the protocol to access its BCTs
    protocols = {
        'employment_support_v1': {
            'label': 'Employment Support Protocol v1.0',
            'bcts': [
                {'bct_id': '1.1', 'label': 'Goal setting (behaviour)', 'class': 'bcio:0000001'},
                {'bct_id': '1.4', 'label': 'Action planning', 'class': 'bcio:0000002'},
                {'bct_id': '1.2', 'label': 'Problem solving', 'class': 'bcio:0000003'},
                {'bct_id': '3.1', 'label': 'Social support (practical)', 'class': 'bcio:0000004'},
                {'bct_id': '2.3', 'label': 'Self-monitoring of behaviour', 'class': 'bcio:0000005'},
                {'bct_id': '15.1', 'label': 'Verbal persuasion about capability', 'class': 'bcio:0000006'},
            ]
        },
        'accommodation_support_v1': {
            'label': 'Accommodation Support Protocol v1.0',
            'bcts': [
                {'bct_id': '12.1', 'label': 'Restructuring physical environment', 'class': 'bcio:0000007'},
                {'bct_id': '3.1', 'label': 'Social support (practical)', 'class': 'bcio:0000004'},
                {'bct_id': '1.4', 'label': 'Action planning', 'class': 'bcio:0000002'},
                {'bct_id': '4.1', 'label': 'Instruction on how to perform behaviour', 'class': 'bcio:0000008'},
            ]
        }
    }
    
    protocol = protocols.get(protocol_id, protocols['employment_support_v1'])
    encounter_id = f'E{datetime.now().strftime("%Y%m%d%H%M%S")}-{participant_id}'
    
    # Build BCT instances from form data
    bct_instances = []
    for bct in protocol['bcts']:
        bct_id = bct['bct_id']
        fidelity_key = f'bct_fidelity_{bct_id}'
        notes_key = f'bct_notes_{bct_id}'
        
        fidelity = request.form.get(fidelity_key, 'delivered')
        notes = request.form.get(notes_key, '')
        
        bct_instance = {
            'bct_instance_uri': f'http://interventions.org/bct/{encounter_id}-{bct_id.replace(".", "_")}',
            'bct_class': bct['class'],
            'bct_id': bct_id,
            'practitioner_label': bct['label'],
            'formal_label': bct['label'],
            'fidelity': {
                'value': fidelity,
                'quality_type': 'bcio:fidelity_quality'
            },
            'notes': notes,
            'auto_tagged': False
        }
        bct_instances.append(bct_instance)
    
    encounter_data = {
        'encounter_uri': f'http://interventions.org/encounter/{encounter_id}',
        'encounter_id': encounter_id,
        'timestamp': datetime.now().isoformat(),
        'delivered_to_uri': f'http://interventions.org/participant/{participant_id}',
        'participant_id': participant_id,
        'mode_of_delivery': request.form.get('mode_of_delivery', 'face_to_face'),
        'duration_minutes': request.form.get('duration_minutes', '60'),
        'protocol_id': protocol_id,
        'protocol_label': protocol['label'],
        'practitioner_id': request.form.get('practitioner_id', 'CLW001'),
        'bcts': bct_instances,
        'encounter_notes': request.form.get('notes', '')
    }
    
    bcio_graph.add_encounter_instance(encounter_data)
    save_graph(graph)
    
    flash(f'Encounter recorded successfully with {len(bct_instances)} BCTs!', 'success')
    return redirect(url_for('encounters_list'))


# ============================================================================
# BARRIER ASSESSMENT
# ============================================================================

@app.route('/assessment/new', methods=['GET', 'POST'])
def new_assessment():
    """Create new barrier assessment"""
    if request.method == 'POST':
        graph = load_graph()
        
        participant_id = request.form.get('participant_id')
        domain = request.form.get('domain')
        timepoint = request.form.get('timepoint')
        
        # Extract barrier scores
        barrier_scores = {}
        for barrier_type in BarrierAssessment.BARRIER_TYPES.keys():
            score = request.form.get(f'barrier_{barrier_type}')
            if score:
                barrier_scores[barrier_type] = int(score)
        
        if timepoint == 'baseline':
            graph.add_barrier_assessment(
                participant_id=participant_id,
                domain=domain,
                timepoint=timepoint,
                barrier_scores=barrier_scores
            )
        else:
            graph.add_follow_up_assessment(
                participant_id=participant_id,
                domain=domain,
                timepoint=timepoint,
                barrier_scores=barrier_scores
            )
        
        save_graph(graph)
        flash('Assessment submitted successfully!', 'success')
        return redirect(url_for('view_participant_progress', participant_id=participant_id))
    
    # Get participants
    graph = load_graph()
    query = """
    PREFIX iao: <http://purl.obolibrary.org/obo/IAO_>
    PREFIX bfo: <http://purl.obolibrary.org/obo/BFO_>
    SELECT ?participant_id WHERE {
        ?p a bfo:0000040 .
        ?p iao:0000578 ?participant_id .
    }
    """
    
    participants = []
    for row in graph.graph.query(query):
        participants.append({
            'id': str(row.participant_id),
            'name': f'Participant {str(row.participant_id)}'
        })
    
    return render_template('barrier_assessment_form.html',
                         participants=participants,
                         barrier_questions=EMPLOYMENT_BARRIERS,
                         domains=BarrierAssessment.DOMAINS,
                         timepoints=BarrierAssessment.TIMEPOINTS)


@app.route('/participant/<participant_id>/progress')
def view_participant_progress(participant_id):
    """View participant's barrier progression"""
    graph = load_graph()
    barriers = graph.get_participant_barriers(participant_id)
    
    # Organize by domain and barrier type
    organized = {}
    for barrier in barriers:
        domain = barrier['domain']
        barrier_type = barrier['label']
        
        if domain not in organized:
            organized[domain] = {}
        if barrier_type not in organized[domain]:
            organized[domain][barrier_type] = []
        
        organized[domain][barrier_type].append({
            'timepoint': barrier['timepoint'],
            'score': barrier['severity_score'],
            'change': barrier.get('change_from_baseline')
        })
    
    # Calculate stats
    followups = [b for b in barriers if b.get('change_from_baseline') is not None]
    
    if followups:
        changes = [b['change_from_baseline'] for b in followups]
        stats = {
            'baseline_only': False,
            'total_barriers': len(followups),
            'improved': len([c for c in changes if c < 0]),
            'stable': len([c for c in changes if c == 0]),
            'worsened': len([c for c in changes if c > 0]),
            'avg_change': sum(changes) / len(changes) if changes else 0
        }
    else:
        stats = {'baseline_only': True}
    
    return render_template('participant_progress.html',
                         participant_id=participant_id,
                         barriers=organized,
                         stats=stats)


# ============================================================================
# ANALYTICS
# ============================================================================

@app.route('/analytics')
def analytics_dashboard():
    """Service-wide analytics dashboard"""
    graph = load_graph()
    
    # Count assessments
    query = """
    PREFIX bcio: <http://purl.obolibrary.org/obo/BCIO_>
    SELECT (COUNT(DISTINCT ?assessment) as ?count) WHERE {
        ?barrier bcio:has_severity_score ?score .
    }
    """
    results = list(graph.graph.query(query))
    total_assessments = int(results[0][0]) // 6 if results else 0  # Divide by 6 barriers
    
    # Average change
    query = """
    PREFIX bcio: <http://purl.obolibrary.org/obo/BCIO_>
    SELECT (AVG(?change) as ?avg_change) WHERE {
        ?barrier bcio:has_change_from_baseline ?change .
    }
    """
    results = list(graph.graph.query(query))
    avg_reduction = float(results[0][0]) if results and results[0][0] else 0
    
    # Change distribution
    query = """
    PREFIX bcio: <http://purl.obolibrary.org/obo/BCIO_>
    SELECT ?change WHERE {
        ?barrier bcio:has_change_from_baseline ?change .
    }
    """
    changes = [int(r[0]) for r in graph.graph.query(query)]
    
    from collections import Counter
    distribution = Counter(changes)
    
    # Safely calculate counts to avoid division by zero
    improved_count = len([c for c in changes if c < 0])
    stable_count = len([c for c in changes if c == 0])
    worsened_count = len([c for c in changes if c > 0])
    
    analytics = {
        'total_assessments': total_assessments,
        'avg_barrier_reduction': avg_reduction,
        'targeted_vs_nontargeted': {
            'targeted_avg': avg_reduction,
            'nontargeted_avg': 0,
            'difference': avg_reduction,
            'abs_difference': abs(avg_reduction)  # Pre-calculate absolute value
        },
        'change_distribution': {
            'changes': changes,
            'distribution': dict(distribution),
            'improved_count': improved_count,
            'stable_count': stable_count,
            'worsened_count': worsened_count,
            'has_data': len(changes) > 0  # Flag to check if we have data
        }
    }
    
    return render_template('analytics_dashboard.html', analytics=analytics)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/barriers/<participant_id>')
def api_get_barriers(participant_id):
    """API endpoint for barrier data"""
    graph = load_graph()
    domain = request.args.get('domain')
    timepoint = request.args.get('timepoint')
    
    barriers = graph.get_participant_barriers(
        participant_id,
        domain=domain,
        timepoint=timepoint
    )
    
    return jsonify(barriers)


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  Intervention Tracking System")
    print("="*60)
    print("\nStarting server on http://localhost:5000")
    print("\nAvailable pages:")
    print("  • http://localhost:5000/ - Home")
    print("  • http://localhost:5000/participants - View participants")
    print("  • http://localhost:5000/participant/new - Add participant")
    print("  • http://localhost:5000/encounters - View encounters")
    print("  • http://localhost:5000/encounter/new - Record encounter")
    print("  • http://localhost:5000/assessment/new - New assessment")
    print("  • http://localhost:5000/analytics - Analytics dashboard")
    print("\n" + "="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
