# Intervention Tracking System

A knowledge graph-based system for tracking behavioral interventions in justice settings using the [Behaviour Change Intervention Ontology (BCIO)](http://humanbehaviourchange.org/ontology/).

## 🎯 Features

- **Participant Management**: Register and track intervention recipients
- **Encounter Recording**: Document intervention sessions with BCT instantiations
- **Barrier Assessment**: Conduct COM-B barrier assessments across 6 categories
- **Progress Tracking**: Visualize participant outcomes over time
- **Analytics Dashboard**: Service-wide analytics showing barrier reduction
- **Knowledge Graph**: RDF-based data storage with SPARQL querying

## 🏗️ Architecture

Built on:
- **Flask** - Web framework
- **RDFLib** - Knowledge graph and semantic web capabilities
- **BCIO Ontology** - Standardized behavioral intervention taxonomy

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/intervention-system.git
cd intervention-system
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Generate demo data** (optional)
```bash
python demo_data_generator.py
```

4. **Run the application**
```bash
python app.py
```

5. **Open your browser**
```
http://localhost:5000
```

## 📊 Available Pages

### Core Functions
- **Home** (`/`) - Main dashboard with navigation
- **Add Participant** (`/participant/new`) - Register new participants
- **Record Encounter** (`/encounter/new`) - Document interventions
- **Barrier Assessment** (`/assessment/new`) - COM-B assessments

### Viewing & Analysis
- **View Participants** (`/participants`) - Browse all participants
- **View Encounters** (`/encounters`) - Review all encounters
- **Analytics Dashboard** (`/analytics`) - Service-wide analytics
- **Participant Progress** (`/participant/<id>/progress`) - Individual progress tracking

## 📖 Usage Guide

### 1. Add a Participant
Navigate to `/participant/new` and enter participant details. The system will:
- Generate a unique participant ID (P001, P002, etc.)
- Create an RDF node in the knowledge graph
- Apply BCIO population tags

### 2. Conduct Baseline Assessment
Navigate to `/assessment/new` and complete the COM-B barrier assessment:
- Select the participant
- Choose domain (employment, accommodation, etc.)
- Select "Baseline" timepoint
- Rate barriers 0-10 across 6 COM-B categories

### 3. Record Interventions
Navigate to `/encounter/new` to document intervention sessions:
- Select participant
- Choose protocol
- Record BCTs delivered with fidelity ratings
- Add practitioner notes

### 4. Follow-up Assessments
Repeat barrier assessments at 30, 90, and 180 days. The system automatically:
- Calculates change scores from baseline
- Links to baseline assessments via ontology relationships
- Visualizes trajectories

### 5. View Analytics
Navigate to `/analytics` to see service-wide metrics:
- Average barrier reduction
- Change score distribution
- Targeted vs non-targeted domains comparison

## 🗄️ Data Storage

All data is stored in a Turtle (.ttl) RDF graph at `data/demo_graph.ttl`.

**Sample SPARQL query:**
```sparql
PREFIX bcio: <http://purl.obolibrary.org/obo/BCIO_>

SELECT ?participant ?change WHERE {
    ?barrier bcio:has_change_from_baseline ?change .
    ?assessment bcio:has_specified_input ?participant .
}
```

## 🧪 Demo Data

Generate synthetic demonstration data:
```bash
python demo_data_generator.py
```

This creates:
- 5 participants with realistic profiles
- Baseline + 3 follow-up assessments each
- 14 intervention encounters per participant
- Diverse outcome scenarios (good/poor/delayed response)

## 📁 Project Structure

```
intervention-system/
├── app.py                          # Main Flask application
├── ontology_core.py                # BCIO graph core functionality
├── barrier_assessment.py           # COM-B barrier assessment module
├── demo_data_generator.py          # Synthetic data generator
├── templates/                      # HTML templates
│   ├── index.html                 # Home page
│   ├── intake_form.html           # Participant registration
│   ├── encounter_form.html        # Encounter recording
│   ├── barrier_assessment_form.html
│   ├── participant_progress.html  # Progress visualization
│   ├── analytics_dashboard.html   # Service analytics
│   └── ...
├── data/                          # RDF graph storage
│   └── demo_graph.ttl
└── requirements.txt               # Python dependencies
```

## 🔧 Configuration

Edit `app.py` to configure:
- `DATA_DIR` - Path to RDF graph storage
- `app.secret_key` - Session secret (change in production!)
- Port (default: 5000)

## 🌐 Deployment

### Local Development
```bash
python app.py
```

### Production (with Gunicorn)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

## 📚 Ontology Resources

- [BCIO Ontology](http://humanbehaviourchange.org/ontology/)
- [BCT Taxonomy v1](https://www.bct-taxonomy.com/)
- [COM-B Model](https://doi.org/10.1186/1748-5908-6-42)

## 🤝 Contributing

This is a prototype/research project. Contributions welcome:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🔬 Citation

If you use this system in research, please cite:

```
Intervention Tracking System using BCIO
Alex McLean, Maximus (2024)
GitHub: [your-repo-url]
```

## 📧 Contact

For questions or collaboration: [your-email]

## 🙏 Acknowledgments

- Built on the [Behaviour Change Intervention Ontology (BCIO)](http://humanbehaviourchange.org/ontology/)
- Uses the [BCT Taxonomy v1](https://www.bct-taxonomy.com/)
- Inspired by implementation science frameworks

---

**Status**: Research Prototype  
**Version**: 1.0.0  
**Last Updated**: November 2024
