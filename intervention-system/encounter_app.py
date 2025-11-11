from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime
import json
import os
from pathlib import Path

from ontology_core import (
    BCIOGraph, 
    JSONLDConverter, 
    TripleStoreManager,
    validate_against_bcio
)

app = Flask(__name__)

DATA_FILE = 'encounters.json'
RDF_EXPORT_DIR = Path('rdf_exports')
JSONLD_EXPORT_DIR = Path('jsonld_exports')

RDF_EXPORT_DIR.mkdir(exist_ok=True)
JSONLD_EXPORT_DIR.mkdir(exist_ok=True)

TRIPLE_STORE_ENDPOINT = None
triple_store = TripleStoreManager(TRIPLE_STORE_ENDPOINT) if TRIPLE_STORE_ENDPOINT else None

ENABLE_RDF_EXPORT = True
ENABLE_JSONLD_EXPORT = True
ENABLE_TRIPLE_STORE = False
ENABLE_VALIDATION = True


def load_encounters():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []


def save_encounters(encounters):
    with open(DATA_FILE, 'w') as f:
        json.dump(encounters, f, indent=2)


def save_encounter_with_rdf(encounter_data):
    encounter_id = encounter_data['encounter_id']
    
    encounters = load_encounters()
    encounters.append(encounter_data)
    save_encounters(encounters)
    
    if ENABLE_RDF_EXPORT:
        try:
            bcio_graph = BCIOGraph()
            bcio_graph.add_encounter_instance(encounter_data)
            
            rdf_file = RDF_EXPORT_DIR / f"{encounter_id}.ttl"
            bcio_graph.save(str(rdf_file), format='turtle')
            
            print(f"✓ RDF export: {rdf_file}")
            
            if ENABLE_VALIDATION:
                validation_results = validate_against_bcio(bcio_graph.graph)
                if validation_results['warnings']:
                    print(f"⚠ Validation warnings: {validation_results['warnings']}")
                if validation_results['errors']:
                    print(f"✗ Validation errors: {validation_results['errors']}")
        
        except Exception as e:
            print(f"RDF export failed: {e}")
    
    if ENABLE_JSONLD_EXPORT:
        try:
            jsonld_data = JSONLDConverter.add_context(encounter_data, 'encounter')
            jsonld_file = JSONLD_EXPORT_DIR / f"{encounter_id}.jsonld"
            with open(jsonld_file, 'w') as f:
                json.dump(jsonld_data, f, indent=2)
            print(f"✓ JSON-LD export: {jsonld_file}")
        except Exception as e:
            print(f"JSON-LD export failed: {e}")
    
    if ENABLE_TRIPLE_STORE and triple_store:
        try:
            bcio_graph = BCIOGraph()
            bcio_graph.add_encounter_instance(encounter_data)
            success = triple_store.upload_graph(bcio_graph.graph)
            if success:
                print(f"✓ Triple store upload: {encounter_id}")
        except Exception as e:
            print(f"Triple store upload failed: {e}")


PROTOCOL_CATALOG = {
    'housing_action_planning': {
        'label': 'Housing Action Planning Session',
        'description': 'Structured session to develop concrete housing stability plan',
        'bcts': [
            {
                'bct_id': 'BCT_1.1',
                'label': 'Goal setting (behavior)',
                'practitioner_label': 'Help participant set specific housing goals',
                'definition': 'Set or agree a goal defined in terms of the behavior to be achieved.',
                'auto': True,
                'bct_class': 'BCIO:007004'
            },
            {
                'bct_id': 'BCT_1.4',
                'label': 'Action planning',
                'practitioner_label': 'Create action plan together',
                'definition': 'Prompt detailed planning of performance of the behavior (when, where, how, and with whom to act).',
                'auto': True,
                'bct_class': 'BCIO:007010'
            },
            {
                'bct_id': 'BCT_3.2',
                'label': 'Social support (practical)',
                'practitioner_label': 'Arrange practical support from others',
                'definition': 'Advise on, arrange, or provide practical help (e.g., from friends, relatives, colleagues, buddies or staff) for performance of the behavior.',
                'auto': False,
                'bct_class': 'BCIO:007030'
            },
            {
                'bct_id': 'BCT_12.5',
                'label': 'Adding objects to the environment',
                'practitioner_label': 'Provide resources or materials',
                'definition': 'Add objects to the environment in order to facilitate performance of the behavior.',
                'auto': False,
                'bct_class': 'BCIO:007156'
            }
        ],
        'typical_mode': 'Face-to-face individual',
        'typical_duration': '30-45 minutes'
    },
    'substance_use_brief_intervention': {
        'label': 'Substance Use Brief Intervention',
        'description': 'Motivational interviewing-based brief intervention for substance use',
        'bcts': [
            {
                'bct_id': 'BCT_5.1',
                'label': 'Information about health consequences',
                'practitioner_label': 'Discuss health impacts of substance use',
                'definition': 'Provide information (e.g., written, verbal, visual) about health consequences of performing the behavior.',
                'auto': True,
                'bct_class': 'BCIO:007054'
            },
            {
                'bct_id': 'BCT_5.3',
                'label': 'Information about social/environmental consequences',
                'practitioner_label': 'Discuss how substance use affects life circumstances',
                'definition': 'Provide information (e.g., written, verbal, visual) about social and environmental consequences of performing the behavior.',
                'auto': True,
                'bct_class': 'BCIO:007056'
            },
            {
                'bct_id': 'BCT_13.2',
                'label': 'Framing/reframing',
                'practitioner_label': 'Help see situation from different perspective',
                'definition': 'Suggest the deliberate adoption of a perspective or new perspective on behavior (e.g., its purpose) in order to change cognitions or emotions about performing the behavior.',
                'auto': False,
                'bct_class': 'BCIO:007174'
            },
            {
                'bct_id': 'BCT_9.2',
                'label': 'Pros and cons',
                'practitioner_label': 'Explore benefits and drawbacks together',
                'definition': 'Advise the person to identify and compare reasons for wanting and not wanting to change the behavior.',
                'auto': True,
                'bct_class': 'BCIO:007100'
            },
            {
                'bct_id': 'BCT_1.5',
                'label': 'Review behavior goals',
                'practitioner_label': 'Check progress on previous goals',
                'definition': 'Review behavior goal(s) jointly with the person and consider modifying goal(s) or behavior change strategy in light of achievement.',
                'auto': False,
                'bct_class': 'BCIO:007013'
            }
        ],
        'typical_mode': 'Face-to-face individual',
        'typical_duration': '15-30 minutes'
    },
    'benefits_navigation': {
        'label': 'Benefits Navigation Support',
        'description': 'Assistance with accessing public benefits and entitlements',
        'bcts': [
            {
                'bct_id': 'BCT_4.1',
                'label': 'Instruction on how to perform behavior',
                'practitioner_label': 'Give step-by-step instructions',
                'definition': 'Advise or agree on how to perform the behavior (includes \'skills training\').',
                'auto': True,
                'bct_class': 'BCIO:007037'
            },
            {
                'bct_id': 'BCT_3.2',
                'label': 'Social support (practical)',
                'practitioner_label': 'Provide hands-on assistance',
                'definition': 'Advise on, arrange, or provide practical help (e.g., from friends, relatives, colleagues, buddies or staff) for performance of the behavior.',
                'auto': True,
                'bct_class': 'BCIO:007030'
            },
            {
                'bct_id': 'BCT_12.5',
                'label': 'Adding objects to the environment',
                'practitioner_label': 'Provide forms or documentation',
                'definition': 'Add objects to the environment in order to facilitate performance of the behavior.',
                'auto': False,
                'bct_class': 'BCIO:007156'
            },
            {
                'bct_id': 'BCT_8.7',
                'label': 'Graded tasks',
                'practitioner_label': 'Break application process into smaller steps',
                'definition': 'Set easy-to-perform tasks, making them increasingly difficult, but achievable, until behavior is performed.',
                'auto': False,
                'bct_class': 'BCIO:007091'
            }
        ],
        'typical_mode': 'Face-to-face individual',
        'typical_duration': '20-40 minutes'
    },
    'crisis_intervention': {
        'label': 'Crisis De-escalation',
        'description': 'Immediate support during acute crisis or emotional distress',
        'bcts': [
            {
                'bct_id': 'BCT_3.1',
                'label': 'Social support (unspecified)',
                'practitioner_label': 'Provide emotional support and presence',
                'definition': 'Advise on, arrange, or provide social support (e.g., from friends, relatives, colleagues, buddies or staff) or non-contingent praise or reward for performance of the behavior.',
                'auto': True,
                'bct_class': 'BCIO:007029'
            },
            {
                'bct_id': 'BCT_11.2',
                'label': 'Reduce negative emotions',
                'practitioner_label': 'Help calm and manage distress',
                'definition': 'Advise on ways of reducing negative emotions to facilitate performance of the behavior.',
                'auto': True,
                'bct_class': 'BCIO:007127'
            },
            {
                'bct_id': 'BCT_15.1',
                'label': 'Verbal persuasion about capability',
                'practitioner_label': 'Build confidence they can get through this',
                'definition': 'Tell the person that they can successfully perform the wanted behavior, arguing against self-doubts and asserting that they can and will succeed.',
                'auto': False,
                'bct_class': 'BCIO:007194'
            },
            {
                'bct_id': 'BCT_12.5',
                'label': 'Adding objects to the environment',
                'practitioner_label': 'Connect to crisis resources',
                'definition': 'Add objects to the environment in order to facilitate performance of the behavior.',
                'auto': False,
                'bct_class': 'BCIO:007156'
            }
        ],
        'typical_mode': 'Face-to-face individual',
        'typical_duration': '10-20 minutes'
    },
    'peer_support_checkin': {
        'label': 'Peer Support Check-in',
        'description': 'Regular check-in with peer support specialist',
        'bcts': [
            {
                'bct_id': 'BCT_3.1',
                'label': 'Social support (unspecified)',
                'practitioner_label': 'Provide supportive presence and listening',
                'definition': 'Advise on, arrange, or provide social support (e.g., from friends, relatives, colleagues, buddies or staff) or non-contingent praise or reward for performance of the behavior.',
                'auto': True,
                'bct_class': 'BCIO:007029'
            },
            {
                'bct_id': 'BCT_1.5',
                'label': 'Review behavior goals',
                'practitioner_label': 'Check in on progress toward goals',
                'definition': 'Review behavior goal(s) jointly with the person and consider modifying goal(s) or behavior change strategy in light of achievement.',
                'auto': False,
                'bct_class': 'BCIO:007013'
            },
            {
                'bct_id': 'BCT_10.9',
                'label': 'Self-reward',
                'practitioner_label': 'Encourage celebrating successes',
                'definition': 'Prompt self-reward if and only if there has been effort and/or progress in performing the behavior.',
                'auto': False,
                'bct_class': 'BCIO:007119'
            },
            {
                'bct_id': 'BCT_15.3',
                'label': 'Focus on past success',
                'practitioner_label': 'Remind of past achievements',
                'definition': 'Advise to think about or list previous successes in performing the behavior.',
                'auto': False,
                'bct_class': 'BCIO:007196'
            }
        ],
        'typical_mode': 'Face-to-face individual',
        'typical_duration': '15-30 minutes'
    },
    'referral_provision': {
        'label': 'Referral to External Service',
        'description': 'Connection to external service provider or organization',
        'bcts': [
            {
                'bct_id': 'BCT_12.5',
                'label': 'Adding objects to the environment',
                'practitioner_label': 'Provide referral information or connection',
                'definition': 'Add objects to the environment in order to facilitate performance of the behavior.',
                'auto': True,
                'bct_class': 'BCIO:007156'
            },
            {
                'bct_id': 'BCT_3.2',
                'label': 'Social support (practical)',
                'practitioner_label': 'Arrange connection to service',
                'definition': 'Advise on, arrange, or provide practical help (e.g., from friends, relatives, colleagues, buddies or staff) for performance of the behavior.',
                'auto': True,
                'bct_class': 'BCIO:007030'
            },
            {
                'bct_id': 'BCT_4.1',
                'label': 'Instruction on how to perform behavior',
                'practitioner_label': 'Explain how to access the service',
                'definition': 'Advise or agree on how to perform the behavior (includes \'skills training\').',
                'auto': False,
                'bct_class': 'BCIO:007037'
            }
        ],
        'typical_mode': 'Face-to-face individual',
        'typical_duration': '5-15 minutes'
    }
}

REFERRAL_CATALOG = {
    'housing': ['Emergency shelter', 'Transitional housing', 'Permanent supportive housing', 'Affordable housing'],
    'mental_health': ['Outpatient MH clinic', 'Crisis stabilization', 'Psychiatric hospitalization', 'Peer support group'],
    'substance_use': ['Detox program', 'Residential treatment', 'Outpatient counseling', 'MAT program', 'Recovery support'],
    'medical': ['Primary care clinic', 'Urgent care', 'Emergency department', 'Specialist referral'],
    'legal': ['Legal aid', 'Public defender', 'Immigration attorney'],
    'employment': ['Job training', 'Job placement', 'Vocational rehab']
}


def generate_bct_uri(encounter_id, bct_index):
    return f"http://interventions.org/encounter/{encounter_id}/bct/{bct_index}"


def auto_tag_encounter(encounter_id, protocol_id, confirmed_bcts, referral_data=None):
    protocol = PROTOCOL_CATALOG.get(protocol_id, {})
    bct_instances = []
    bct_index = 0
    
    for bct_def in protocol.get('bcts', []):
        bct_id = bct_def['bct_id']
        
        if bct_id in confirmed_bcts:
            bct_index += 1
            fidelity = confirmed_bcts[bct_id].get('fidelity', 'not_assessed')
            notes = confirmed_bcts[bct_id].get('notes', '')
            
            bct_instance = {
                'bct_instance_uri': generate_bct_uri(encounter_id, bct_index),
                'bct_class': bct_def['bct_class'],
                'bct_id': bct_id,
                'practitioner_label': bct_def['practitioner_label'],
                'formal_label': bct_def['label'],
                'fidelity': {
                    'value': fidelity,
                    'quality_type': f'bcio:Fidelity_{fidelity}'
                },
                'notes': notes,
                'auto_tagged': bct_def['auto']
            }
            
            bct_instances.append(bct_instance)
    
    if referral_data and referral_data.get('was_referral_made'):
        if not any('BCT_12.5' in b['bct_id'] for b in bct_instances):
            bct_index += 1
            bct_instances.append({
                'bct_instance_uri': generate_bct_uri(encounter_id, bct_index),
                'bct_class': 'BCIO:007156',
                'bct_id': 'BCT_12.5',
                'practitioner_label': 'Provide referral information or connection',
                'formal_label': 'Adding objects to the environment',
                'fidelity': {
                    'value': 'delivered',
                    'quality_type': 'bcio:Fidelity_delivered'
                },
                'notes': f"Referral to {referral_data.get('category', 'unspecified')}",
                'auto_tagged': True,
                'referral_context': referral_data
            })
    
    return bct_instances


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/encounter/new')
def new_encounter():
    return render_template('encounter_form.html', 
                         protocols=PROTOCOL_CATALOG,
                         referral_catalog=REFERRAL_CATALOG)


@app.route('/encounter/submit', methods=['POST'])
def submit_encounter():
    encounter_id = f"ENC_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    encounter_uri = f"http://interventions.org/encounter/{encounter_id}"
    
    participant_id = request.form.get('participant_id')
    participant_uri = f"http://interventions.org/participant/{participant_id}"
    
    encounter_data = {
        'encounter_uri': encounter_uri,
        'encounter_id': encounter_id,
        'encounter_type': 'bcio:BCI_scenario',
        'timestamp': datetime.now().isoformat(),
        'practitioner_id': request.form.get('practitioner_id'),
        'participant_id': participant_id,
        'delivered_to_uri': participant_uri,
        'protocol_id': request.form.get('protocol_id'),
        'protocol_label': PROTOCOL_CATALOG[request.form.get('protocol_id')]['label'],
        'mode_of_delivery': request.form.get('mode_of_delivery'),
        'duration_minutes': request.form.get('duration_minutes'),
        'encounter_notes': request.form.get('encounter_notes', '')
    }
    
    confirmed_bcts = {}
    for key, value in request.form.items():
        if key.startswith('bct_fidelity_'):
            bct_id = key.replace('bct_fidelity_', '')
            confirmed_bcts[bct_id] = {
                'fidelity': value,
                'notes': request.form.get(f'bct_notes_{bct_id}', '')
            }
    
    referral_data = None
    if request.form.get('was_referral_made') == 'yes':
        referral_data = {
            'was_referral_made': True,
            'category': request.form.get('referral_category'),
            'destination': request.form.get('referral_destination'),
            'accepted': request.form.get('referral_accepted') == 'yes'
        }
        encounter_data['referral'] = referral_data
    
    bct_instances = auto_tag_encounter(
        encounter_id=encounter_id,
        protocol_id=encounter_data['protocol_id'],
        confirmed_bcts=confirmed_bcts,
        referral_data=referral_data
    )
    
    encounter_data['bcts'] = bct_instances
    encounter_data['num_bcts'] = len(bct_instances)
    
    save_encounter_with_rdf(encounter_data)
    
    return redirect(url_for('view_encounters'))


@app.route('/encounters')
def view_encounters():
    encounters = load_encounters()
    return render_template('view_encounters.html', encounters=encounters)


@app.route('/participant/<participant_id>/encounters')
def participant_encounters(participant_id):
    participant_uri = f"http://interventions.org/participant/{participant_id}"
    all_encounters = load_encounters()
    
    participant_encounters = [
        e for e in all_encounters 
        if e.get('delivered_to_uri') == participant_uri
    ]
    
    return render_template('participant_encounters.html', 
                          participant_id=participant_id,
                          encounters=participant_encounters)


@app.route('/api/protocol/<protocol_id>')
def get_protocol_details(protocol_id):
    protocol = PROTOCOL_CATALOG.get(protocol_id)
    if protocol:
        return jsonify(protocol)
    return jsonify({'error': 'Protocol not found'}), 404


@app.route('/api/encounters/rdf/<encounter_id>')
def get_encounter_rdf(encounter_id):
    rdf_file = RDF_EXPORT_DIR / f"{encounter_id}.ttl"
    if rdf_file.exists():
        with open(rdf_file, 'r') as f:
            return f.read(), 200, {'Content-Type': 'text/turtle'}
    return jsonify({'error': 'RDF export not found'}), 404


@app.route('/api/encounters/jsonld/<encounter_id>')
def get_encounter_jsonld(encounter_id):
    jsonld_file = JSONLD_EXPORT_DIR / f"{encounter_id}.jsonld"
    if jsonld_file.exists():
        with open(jsonld_file, 'r') as f:
            return f.read(), 200, {'Content-Type': 'application/ld+json'}
    return jsonify({'error': 'JSON-LD export not found'}), 404


if __name__ == '__main__':
    print("\n" + "="*70)
    print("BCIO INTERVENTION ENCOUNTER CAPTURE")
    print("="*70)
    print("\nFeatures enabled:")
    print(f"  • RDF Export (Turtle): {ENABLE_RDF_EXPORT}")
    print(f"  • JSON-LD Export: {ENABLE_JSONLD_EXPORT}")
    print(f"  • Triple Store: {ENABLE_TRIPLE_STORE}")
    print(f"  • Ontology Validation: {ENABLE_VALIDATION}")
    print("\nExport locations:")
    print(f"  • RDF: {RDF_EXPORT_DIR}/")
    print(f"  • JSON-LD: {JSONLD_EXPORT_DIR}/")
    print("\nStarting server on http://127.0.0.1:5001")
    print("Press CTRL+C to stop")
    print("="*70 + "\n")
    
    app.run(debug=True, port=5001)
