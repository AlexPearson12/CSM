"""
Barrier Assessment Flask App
Integrates with existing participant intake system
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify
from barrier_assessment import (
    BarrierAssessmentGraph, BarrierAssessment, EMPLOYMENT_BARRIERS
)
from ontology_core import BCIOGraph
import json
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

# Storage paths
DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)
GRAPH_FILE = DATA_DIR / 'demo_graph.ttl'  # Use demo data file


def load_graph():
    """Load existing graph or create new one"""
    graph = BarrierAssessmentGraph()
    if GRAPH_FILE.exists():
        graph.graph.parse(GRAPH_FILE, format='turtle')
    return graph


def save_graph(graph):
    """Persist graph to disk"""
    graph.graph.serialize(destination=str(GRAPH_FILE), format='turtle')


@app.route('/assessment/new')
def new_assessment():
    """Form to create new barrier assessment"""
    
    # Get list of participants (would integrate with your participant system)
    participants = get_participants()
    
    return render_template('barrier_assessment_form.html',
                         participants=participants,
                         barrier_questions=EMPLOYMENT_BARRIERS,
                         domains=BarrierAssessment.DOMAINS,
                         timepoints=BarrierAssessment.TIMEPOINTS)


@app.route('/assessment/submit', methods=['POST'])
def submit_assessment():
    """Process barrier assessment submission"""
    
    data = request.form
    
    participant_id = data.get('participant_id')
    domain = data.get('domain')
    timepoint = data.get('timepoint')
    
    # Extract barrier scores
    barrier_scores = {}
    for barrier_type in BarrierAssessment.BARRIER_TYPES.keys():
        score = data.get(f'barrier_{barrier_type}')
        if score:
            barrier_scores[barrier_type] = int(score)
    
    # Load graph and add assessment
    graph = load_graph()
    
    if timepoint == 'baseline':
        assessment_uri = graph.add_barrier_assessment(
            participant_id=participant_id,
            domain=domain,
            timepoint=timepoint,
            barrier_scores=barrier_scores
        )
    else:
        # Follow-up assessment - auto-calculate changes
        assessment_uri = graph.add_follow_up_assessment(
            participant_id=participant_id,
            domain=domain,
            timepoint=timepoint,
            barrier_scores=barrier_scores
        )
    
    save_graph(graph)
    
    return redirect(url_for('view_participant_progress', 
                           participant_id=participant_id))


@app.route('/participant/<participant_id>/progress')
def view_participant_progress(participant_id):
    """View participant's barrier progression over time"""
    
    graph = load_graph()
    
    # Get all barriers for this participant
    barriers = graph.get_participant_barriers(participant_id)
    
    # Organize by domain and timepoint for visualization
    organized = organize_barriers_for_display(barriers)
    
    # Calculate summary stats
    stats = calculate_progress_stats(barriers)
    
    return render_template('participant_progress.html',
                         participant_id=participant_id,
                         barriers=organized,
                         stats=stats)


@app.route('/api/barriers/<participant_id>')
def api_get_barriers(participant_id):
    """API endpoint for barrier data (for charts/dashboards)"""
    
    graph = load_graph()
    domain = request.args.get('domain')
    timepoint = request.args.get('timepoint')
    
    barriers = graph.get_participant_barriers(
        participant_id, 
        domain=domain,
        timepoint=timepoint
    )
    
    return jsonify(barriers)


@app.route('/analytics/dashboard')
def analytics_dashboard():
    """
    Service-wide analytics dashboard showing:
    - Average barrier reduction by domain
    - Targeted vs non-targeted domain comparison  
    - Distribution of change scores
    """
    
    graph = load_graph()
    
    # Run analytical queries
    analytics = {
        'total_assessments': count_total_assessments(graph),
        'avg_barrier_reduction': calculate_avg_barrier_reduction(graph),
        'targeted_vs_nontargeted': compare_targeted_domains(graph),
        'change_distribution': get_change_score_distribution(graph)
    }
    
    return render_template('analytics_dashboard.html', 
                         analytics=analytics)


def organize_barriers_for_display(barriers):
    """
    Organize barriers by domain and barrier type for easy visualization.
    Returns nested dict: {domain: {barrier_type: [timepoint_data]}}
    """
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
    
    return organized


def calculate_progress_stats(barriers):
    """Calculate summary statistics for participant progress"""
    
    if not barriers:
        return None
    
    # Filter to follow-up assessments only (have change scores)
    followups = [b for b in barriers if b.get('change_from_baseline') is not None]
    
    if not followups:
        return {'baseline_only': True}
    
    changes = [b['change_from_baseline'] for b in followups]
    
    stats = {
        'baseline_only': False,
        'total_barriers': len(followups),
        'improved': len([c for c in changes if c < 0]),
        'stable': len([c for c in changes if c == 0]),
        'worsened': len([c for c in changes if c > 0]),
        'avg_change': sum(changes) / len(changes),
        'max_improvement': min(changes),  # Most negative = best improvement
        'max_worsening': max(changes)
    }
    
    return stats


def count_total_assessments(graph):
    """Count all barrier assessments in system"""
    query = """
    PREFIX bcio: <http://purl.obolibrary.org/obo/BCIO_>
    SELECT (COUNT(DISTINCT ?assessment) as ?count) WHERE {
        ?assessment a bcio:0000001 .
        ?assessment bcio:has_temporal_value ?date .
    }
    """
    results = list(graph.graph.query(query))
    return int(results[0][0]) if results else 0


def calculate_avg_barrier_reduction(graph):
    """Calculate average barrier reduction across all participants"""
    query = """
    PREFIX bcio: <http://purl.obolibrary.org/obo/BCIO_>
    SELECT (AVG(?change) as ?avg_change) WHERE {
        ?barrier bcio:has_change_from_baseline ?change .
    }
    """
    results = list(graph.graph.query(query))
    return float(results[0][0]) if results and results[0][0] else 0


def compare_targeted_domains(graph):
    """
    Compare change in targeted vs non-targeted domains.
    
    For prototype, assume employment is targeted, others non-targeted.
    In full system, this would query intervention records.
    """
    
    # Query employment (targeted) change
    targeted_query = """
    PREFIX bcio: <http://purl.obolibrary.org/obo/BCIO_>
    PREFIX intervention: <http://interventions.org/>
    SELECT (AVG(?change) as ?avg_change) WHERE {
        ?barrier bcio:has_change_from_baseline ?change .
        ?barrier bcio:concerns_domain <http://interventions.org/domain/Employment_Domain> .
    }
    """
    
    # Query other domains (non-targeted) change  
    nontargeted_query = """
    PREFIX bcio: <http://purl.obolibrary.org/obo/BCIO_>
    PREFIX intervention: <http://interventions.org/>
    SELECT (AVG(?change) as ?avg_change) WHERE {
        ?barrier bcio:has_change_from_baseline ?change .
        ?barrier bcio:concerns_domain ?domain .
        FILTER(?domain != <http://interventions.org/domain/Employment_Domain>)
    }
    """
    
    targeted_results = list(graph.graph.query(targeted_query))
    nontargeted_results = list(graph.graph.query(nontargeted_query))
    
    targeted_avg = float(targeted_results[0][0]) if targeted_results and targeted_results[0][0] else 0
    nontargeted_avg = float(nontargeted_results[0][0]) if nontargeted_results and nontargeted_results[0][0] else 0
    
    return {
        'targeted_avg': targeted_avg,
        'nontargeted_avg': nontargeted_avg,
        'difference': targeted_avg - nontargeted_avg
    }


def get_change_score_distribution(graph):
    """Get distribution of change scores for histogram"""
    query = """
    PREFIX bcio: <http://purl.obolibrary.org/obo/BCIO_>
    SELECT ?change WHERE {
        ?barrier bcio:has_change_from_baseline ?change .
    }
    ORDER BY ?change
    """
    
    results = list(graph.graph.query(query))
    changes = [int(r[0]) for r in results]
    
    # Create bins for histogram
    from collections import Counter
    distribution = Counter(changes)
    
    return {
        'changes': changes,
        'distribution': dict(distribution),
        'improved_count': len([c for c in changes if c < 0]),
        'stable_count': len([c for c in changes if c == 0]),
        'worsened_count': len([c for c in changes if c > 0])
    }


def get_participants():
    """
    Get list of participants.
    In production, this would query your participant database.
    For prototype, return mock data or integrate with your participant_intake_app.
    """
    # This would integrate with your existing participant system
    return [
        {'id': 'P001', 'name': 'Participant 001'},
        {'id': 'P002', 'name': 'Participant 002'},
        {'id': 'P003', 'name': 'Participant 003'}
    ]


if __name__ == '__main__':
    app.run(debug=True, port=5001)
