from flask import Flask, render_template, request, jsonify
import sqlite3
import json
from datetime import datetime, date
from pathlib import Path
import uuid

from ontology_core import (
    BCIOGraph,
    JSONLDConverter,
    TripleStoreManager,
    validate_against_bcio
)

app = Flask(__name__)

DB_FILE = 'participants.db'
RDF_EXPORT_DIR = Path('rdf_exports/participants')
JSONLD_EXPORT_DIR = Path('jsonld_exports/participants')

RDF_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
JSONLD_EXPORT_DIR.mkdir(parents=True, exist_ok=True)

ENABLE_RDF_EXPORT = True
ENABLE_JSONLD_EXPORT = True
ENABLE_TRIPLE_STORE = False
ENABLE_VALIDATION = True

TRIPLE_STORE_ENDPOINT = None
triple_store = TripleStoreManager(TRIPLE_STORE_ENDPOINT) if TRIPLE_STORE_ENDPOINT else None


def generate_participant_uri(participant_id):
    return f"http://interventions.org/participant/{participant_id}"


BCIO_DEFINITIONS = {
    "teenager": "A person between 13 and 19 years of age (ADDICTO:0001050)",
    "young_adult": "A person between 18 and 25 years of age",
    "adult": "A person who has reached maturity (ADDICTO:0000352)",
    "ex_offender_population": "A BCI participant who has been released from incarceration and is undergoing community reintegration",
    "recently_released": "A person within 90 days of release from incarceration",
    "homeless_population": "A person with no fixed address or stable housing",
    "housed_population": "A person residing in permanent housing",
    "renter": "A person who lives in a residential facility they do not own in return for paying an agreed sum of money to the residential facility owner (BCIO:015030)",
    "renter_from_social_provider": "A renter who lives in a residential facility where the residential facility owner decides who can live in the residential facility based on their perceived social or economic needs (BCIO:015031)",
    "owner_occupier": "A person who lives in a residential facility of which they are the residential facility owner (BCIO:015029)",
    "substance_use_history": "A person who has a history of substance use",
    "disabled": "A personal attribute in which the person has impaired physical or mental functioning that has a notable effect on their ability to do typical daily activities (BCIO:050474)",
    "long_term_disabled": "Disabled for at least 12 months (BCIO:050479)",
    "medication_use_status": "A health status attribute that is having been prescribed the use of one or more drugs to improve, maintain or protect one's health (BCIO:015093)",
    "achieved_primary_education": "A highest level of formal educational qualification achieved after participating in an education process intended to result in the acquisition of fundamental skills in reading, writing and mathematics (BCIO:015046)",
    "achieved_lower_secondary_education": "A highest level of formal educational qualification achieved after participating in an education process intended to result in the acquisition and development of skills and knowledge in subject areas more specialised than basic reading, writing and mathematics (BCIO:015047)",
    "achieved_upper_secondary_education": "A highest level of formal educational qualification achieved after participating in an education process intended to result in the acquisition and development of skills and knowledge that prepare participants for tertiary education or employment (BCIO:015048)",
    "achieved_bachelors_degree": "A highest level of formal education qualification achieved after participating in an education process intended to result in the acquisition and development of skills and knowledge in a specialised discipline that culminated in the award of an undergraduate degree (BCIO:015049)",
    "achieved_masters_level": "A highest level of formal educational qualification achieved after participating in an education process which has as a prerequisite an undergraduate degree and which is intended to result in the acquisition and development of advanced academic or professional skills and knowledge in a specialised discipline (BCIO:015050)",
    "achieved_doctoral_level": "A highest level of formal educational qualification achieved after participating in an education process devoted to advanced study and original research that led to the award of a PhD or equivalent level qualification (BCIO:015051)",
    "single": "A relationship status where the individual is not in a relationship with another person (BCIO:015072)",
    "in_legal_marriage": "A relationship status where the individual is in a legally formalised marriage or civil partnership (BCIO:015074)",
    "in_stable_relationship": "A relationship status where the individual has had the same partner for a significant length of time but is not in a legal union (BCIO:015073)",
    "divorced_or_separated": "A relationship status where the individual was previously in a legally formalised relationship and this relationship has now ended or dissolved (BCIO:015075)",
    "widowed": "A relationship status where the individual is no longer in a legally formalised marriage or civil partnership due to the death of their spouse or partner (BCIO:015076)"
}


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS participants
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  participant_id TEXT UNIQUE NOT NULL,
                  participant_uri TEXT UNIQUE,
                  created_date TEXT NOT NULL,
                  dob TEXT,
                  age INTEGER,
                  gender TEXT,
                  release_date TEXT,
                  days_since_release INTEGER,
                  supervision_status TEXT,
                  housing_status TEXT,
                  housing_type TEXT,
                  substances JSON,
                  current_substance_use TEXT,
                  mental_health JSON,
                  disability_status TEXT,
                  disability_duration TEXT,
                  medication_use TEXT,
                  medication_types JSON,
                  education_level TEXT,
                  relationship_status TEXT,
                  employment_status TEXT)''')
    
    try:
        c.execute("SELECT participant_uri FROM participants LIMIT 1")
        c.execute("SELECT participant_id FROM participants WHERE participant_uri IS NULL")
        rows = c.fetchall()
        for row in rows:
            participant_id = row[0]
            participant_uri = generate_participant_uri(participant_id)
            c.execute("UPDATE participants SET participant_uri = ? WHERE participant_id = ?",
                     (participant_uri, participant_id))
        conn.commit()
    except sqlite3.OperationalError:
        try:
            c.execute("ALTER TABLE participants ADD COLUMN participant_uri TEXT UNIQUE")
            c.execute("SELECT participant_id FROM participants")
            rows = c.fetchall()
            for row in rows:
                participant_id = row[0]
                participant_uri = generate_participant_uri(participant_id)
                c.execute("UPDATE participants SET participant_uri = ? WHERE participant_id = ?",
                         (participant_uri, participant_id))
            conn.commit()
        except sqlite3.OperationalError:
            pass
    
    c.execute('''CREATE TABLE IF NOT EXISTS bcio_tags
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  participant_id TEXT NOT NULL,
                  tag_name TEXT NOT NULL,
                  tag_category TEXT NOT NULL,
                  bcio_id TEXT,
                  FOREIGN KEY (participant_id) REFERENCES participants (participant_id))''')
    
    conn.commit()
    conn.close()


def calculate_age(dob_string):
    dob = datetime.strptime(dob_string, '%Y-%m-%d').date()
    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return age


def calculate_days_since_release(release_date_string):
    release_date = datetime.strptime(release_date_string, '%Y-%m-%d').date()
    today = date.today()
    return (today - release_date).days


def generate_bcio_attributes(form_data):
    attributes = []
    
    age = form_data['age']
    if 13 <= age <= 19:
        attributes.append(('teenager', 'age', 'ADDICTO:0001050'))
    if 18 <= age <= 25:
        attributes.append(('young_adult', 'age', 'BCIO:0000201'))
    if age >= 18:
        attributes.append(('adult', 'age', 'ADDICTO:0000352'))
    
    if form_data['gender'] and form_data['gender'] != 'prefer_not_say':
        attributes.append((f"{form_data['gender']}_gender", 'gender', f"PATO:{form_data['gender']}_sex"))
    
    attributes.append(('ex_offender_population', 'reentry', 'BCIO:0000202'))
    
    days_since = form_data['days_since_release']
    if days_since <= 90:
        attributes.append(('recently_released', 'reentry', 'BCIO:0000203'))
    if days_since <= 30:
        attributes.append(('first_month_post_release', 'reentry', 'BCIO:0000204'))
    
    if form_data['supervision_status'] != 'none':
        attributes.append(('under_supervision', 'reentry', 'BCIO:0000205'))
        attributes.append((form_data['supervision_status'], 'reentry', 
                         f"BCIO:supervision_{form_data['supervision_status']}"))
    
    housing = form_data['housing_status']
    housing_map = {
        'homeless': ('homeless_population', 'BCIO:0000206'),
        'stable': ('housed_population', 'BCIO:0000207'),
        'transitional': ('transitional_housing_population', 'BCIO:0000208'),
        'institutional': ('institutional_setting_occupant', 'BCIO:0000209')
    }
    if housing in housing_map:
        attr_name, bcio_id = housing_map[housing]
        attributes.append((attr_name, 'housing', bcio_id))
    
    if housing == 'stable' and form_data.get('housing_type'):
        housing_type_map = {
            'owns': ('owner_occupier', 'BCIO:015029'),
            'rents_private': ('renter', 'BCIO:015030'),
            'rents_social': ('renter_from_social_provider', 'BCIO:015031'),
            'family': ('family_household_member', 'BCIO:0000210'),
            'employer': ('employer_provided_housing', 'BCIO:015035')
        }
        if form_data['housing_type'] in housing_type_map:
            attr_name, bcio_id = housing_type_map[form_data['housing_type']]
            attributes.append((attr_name, 'housing', bcio_id))
    
    substances = form_data.get('substances', [])
    if substances and 'none' not in substances:
        attributes.append(('substance_use_history_population', 'health', 'BCIO:0000211'))
        
        substance_map = {
            'alcohol': ('alcohol_use_history', 'BCIO:0000212'),
            'opioids': ('opioid_use_history', 'BCIO:0000213'),
            'stimulants': ('stimulant_use_history', 'BCIO:0000214'),
            'cannabis': ('cannabis_use_history', 'BCIO:0000215')
        }
        for substance in substances:
            if substance in substance_map:
                attr_name, bcio_id = substance_map[substance]
                attributes.append((attr_name, 'health', bcio_id))
        
        if form_data.get('current_substance_use') == 'recovery':
            attributes.append(('substance_use_recovery', 'health', 'BCIO:0000216'))
        elif form_data.get('current_substance_use') == 'currently_using':
            attributes.append(('active_substance_use', 'health', 'BCIO:0000217'))
    
    mental_health = form_data.get('mental_health', [])
    if mental_health and 'none' not in mental_health:
        for condition in mental_health:
            if condition != 'none':
                attributes.append((f'disclosed_{condition}', 'health', f'DOID:{condition}'))
    
    if form_data.get('disability_status') == 'has_disability':
        attributes.append(('disabled', 'health', 'BCIO:050474'))
        if form_data.get('disability_duration') == 'long_term':
            attributes.append(('long_term_disabled', 'health', 'BCIO:050479'))
    
    if form_data.get('medication_use') == 'yes':
        attributes.append(('medication_use_status', 'health', 'BCIO:015093'))
        
        med_types = form_data.get('medication_types', [])
        for med_type in med_types:
            attributes.append((f'{med_type}_medication', 'health', f'BCIO:med_{med_type}'))
    
    education_map = {
        'primary': ('achieved_primary_education', 'BCIO:015046'),
        'lower_secondary': ('achieved_lower_secondary_education', 'BCIO:015047'),
        'upper_secondary': ('achieved_upper_secondary_education', 'BCIO:015048'),
        'bachelors': ('achieved_bachelors_degree', 'BCIO:015049'),
        'masters': ('achieved_masters_level', 'BCIO:015050'),
        'doctoral': ('achieved_doctoral_level', 'BCIO:015051')
    }
    if form_data.get('education_level') in education_map:
        attr_name, bcio_id = education_map[form_data['education_level']]
        attributes.append((attr_name, 'education', bcio_id))
    
    relationship_map = {
        'single': ('single', 'BCIO:015072'),
        'married': ('in_legal_marriage', 'BCIO:015074'),
        'relationship': ('in_stable_relationship', 'BCIO:015073'),
        'divorced': ('divorced_or_separated', 'BCIO:015075'),
        'widowed': ('widowed', 'BCIO:015076')
    }
    if form_data.get('relationship_status') in relationship_map:
        attr_name, bcio_id = relationship_map[form_data['relationship_status']]
        attributes.append((attr_name, 'relationship', bcio_id))
    
    employment = form_data.get('employment_status')
    if employment in ['full_time', 'part_time']:
        attributes.append(('employed', 'employment', 'BCIO:0000220'))
    elif employment == 'unemployed_seeking':
        attributes.append(('unemployed', 'employment', 'BCIO:0000221'))
        attributes.append(('job_seeking', 'employment', 'BCIO:0000222'))
    elif employment == 'unable':
        attributes.append(('unable_to_work', 'employment', 'BCIO:0000223'))
    
    return attributes


def save_participant_with_rdf(participant_data, attribute_data):
    participant_id = participant_data['participant_id']
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    try:
        c.execute('''INSERT INTO participants 
                     (participant_id, participant_uri, created_date, dob, age, gender, release_date, 
                      days_since_release, supervision_status, housing_status, housing_type,
                      substances, current_substance_use, mental_health, disability_status,
                      disability_duration, medication_use, medication_types, education_level,
                      relationship_status, employment_status)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  tuple(participant_data.values()))
        
        for attr_name, attr_category, bcio_id in attribute_data:
            c.execute('''INSERT INTO bcio_tags (participant_id, tag_name, tag_category, bcio_id)
                        VALUES (?, ?, ?, ?)''',
                     (participant_id, attr_name, attr_category, bcio_id))
        
        conn.commit()
        
    finally:
        conn.close()
    
    if ENABLE_RDF_EXPORT:
        try:
            rdf_data = {
                **participant_data,
                'tags': [
                    {
                        'tag_name': name,
                        'tag_category': cat,
                        'bcio_id': bcio_id
                    }
                    for name, cat, bcio_id in attribute_data
                ]
            }
            
            bcio_graph = BCIOGraph()
            bcio_graph.add_participant_instance(rdf_data)
            
            rdf_file = RDF_EXPORT_DIR / f"{participant_id}.ttl"
            bcio_graph.save(str(rdf_file), format='turtle')
            
            print(f"✓ RDF export: {rdf_file}")
            
            if ENABLE_VALIDATION:
                validation_results = validate_against_bcio(bcio_graph.graph)
                if validation_results['warnings']:
                    print(f"⚠ Validation warnings: {validation_results['warnings']}")
        
        except Exception as e:
            print(f"RDF export failed: {e}")
    
    if ENABLE_JSONLD_EXPORT:
        try:
            rdf_data = {
                **participant_data,
                'tags': [
                    {'tag_name': name, 'tag_category': cat, 'bcio_id': bcio_id}
                    for name, cat, bcio_id in attribute_data
                ]
            }
            
            jsonld_data = JSONLDConverter.add_context(rdf_data, 'participant')
            jsonld_file = JSONLD_EXPORT_DIR / f"{participant_id}.jsonld"
            with open(jsonld_file, 'w') as f:
                json.dump(jsonld_data, f, indent=2)
            
            print(f"✓ JSON-LD export: {jsonld_file}")
        
        except Exception as e:
            print(f"JSON-LD export failed: {e}")
    
    if ENABLE_TRIPLE_STORE and triple_store:
        try:
            bcio_graph = BCIOGraph()
            rdf_data = {
                **participant_data,
                'tags': [
                    {'tag_name': name, 'tag_category': cat, 'bcio_id': bcio_id}
                    for name, cat, bcio_id in attribute_data
                ]
            }
            bcio_graph.add_participant_instance(rdf_data)
            
            success = triple_store.upload_graph(bcio_graph.graph)
            if success:
                print(f"✓ Triple store upload: {participant_id}")
        
        except Exception as e:
            print(f"Triple store upload failed: {e}")


@app.route('/')
def index():
    return render_template('intake_form.html', definitions=BCIO_DEFINITIONS)


@app.route('/submit', methods=['POST'])
def submit_form():
    try:
        data = request.json
        
        date_part = datetime.now().strftime('%Y%m%d')
        unique_part = str(uuid.uuid4())[:8]
        participant_id = f"P-{date_part}-{unique_part}"
        
        age = calculate_age(data['dob'])
        days_since_release = calculate_days_since_release(data['release_date'])
        
        form_data = {
            'age': age,
            'gender': data.get('gender'),
            'days_since_release': days_since_release,
            'supervision_status': data.get('supervision_status'),
            'housing_status': data.get('housing_status'),
            'housing_type': data.get('housing_type'),
            'substances': data.get('substances', []),
            'current_substance_use': data.get('current_substance_use'),
            'mental_health': data.get('mental_health', []),
            'disability_status': data.get('disability_status'),
            'disability_duration': data.get('disability_duration'),
            'medication_use': data.get('medication_use'),
            'medication_types': data.get('medication_types', []),
            'education_level': data.get('education_level'),
            'relationship_status': data.get('relationship_status'),
            'employment_status': data.get('employment_status')
        }
        
        bcio_attributes = generate_bcio_attributes(form_data)
        
        participant_uri = generate_participant_uri(participant_id)
        
        participant_data = {
            'participant_id': participant_id,
            'participant_uri': participant_uri,
            'created_date': datetime.now().isoformat(),
            'dob': data['dob'],
            'age': age,
            'gender': data.get('gender'),
            'release_date': data['release_date'],
            'days_since_release': days_since_release,
            'supervision_status': data.get('supervision_status'),
            'housing_status': data.get('housing_status'),
            'housing_type': data.get('housing_type'),
            'substances': json.dumps(data.get('substances', [])),
            'current_substance_use': data.get('current_substance_use'),
            'mental_health': json.dumps(data.get('mental_health', [])),
            'disability_status': data.get('disability_status'),
            'disability_duration': data.get('disability_duration'),
            'medication_use': data.get('medication_use'),
            'medication_types': json.dumps(data.get('medication_types', [])),
            'education_level': data.get('education_level'),
            'relationship_status': data.get('relationship_status'),
            'employment_status': data.get('employment_status')
        }
        
        save_participant_with_rdf(participant_data, bcio_attributes)
        
        return jsonify({
            'success': True,
            'participant_id': participant_id,
            'participant_uri': participant_uri,
            'bcio_tags': [
                {'name': t[0], 'category': t[1], 'id': t[2]} 
                for t in bcio_attributes
            ],
            'tag_count': len(bcio_attributes)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/participants')
def view_participants():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('SELECT * FROM participants ORDER BY created_date DESC')
    participants = [dict(row) for row in c.fetchall()]
    
    for participant in participants:
        c.execute('SELECT * FROM bcio_tags WHERE participant_id = ?', 
                 (participant['participant_id'],))
        participant['tags'] = [dict(row) for row in c.fetchall()]
        
        participant['substances'] = json.loads(participant['substances']) if participant['substances'] else []
        participant['mental_health'] = json.loads(participant['mental_health']) if participant['mental_health'] else []
        participant['medication_types'] = json.loads(participant['medication_types']) if participant['medication_types'] else []
    
    conn.close()
    
    return render_template('view_participants.html', participants=participants)


@app.route('/api/participants/rdf/<participant_id>')
def get_participant_rdf(participant_id):
    rdf_file = RDF_EXPORT_DIR / f"{participant_id}.ttl"
    if rdf_file.exists():
        with open(rdf_file, 'r') as f:
            return f.read(), 200, {'Content-Type': 'text/turtle'}
    return jsonify({'error': 'RDF export not found'}), 404


@app.route('/api/participants/jsonld/<participant_id>')
def get_participant_jsonld(participant_id):
    jsonld_file = JSONLD_EXPORT_DIR / f"{participant_id}.jsonld"
    if jsonld_file.exists():
        with open(jsonld_file, 'r') as f:
            return f.read(), 200, {'Content-Type': 'application/ld+json'}
    return jsonify({'error': 'JSON-LD export not found'}), 404


if __name__ == '__main__':
    init_db()
    
    print("\n" + "="*70)
    print("PARTICIPANT INTAKE FORM")
    print("="*70)
    print("\nFeatures enabled:")
    print(f"  • RDF Export (Turtle): {ENABLE_RDF_EXPORT}")
    print(f"  • JSON-LD Export: {ENABLE_JSONLD_EXPORT}")
    print(f"  • Triple Store: {ENABLE_TRIPLE_STORE}")
    print(f"  • Ontology Validation: {ENABLE_VALIDATION}")
    print("\nExport locations:")
    print(f"  • RDF: {RDF_EXPORT_DIR}/")
    print(f"  • JSON-LD: {JSONLD_EXPORT_DIR}/")
    print("\nStarting server on http://127.0.0.1:5000")
    print("View all participants at: http://127.0.0.1:5000/participants")
    print("Press CTRL+C to stop")
    print("="*70 + "\n")
    
    app.run(debug=True, port=5000)
