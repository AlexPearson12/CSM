# ⚡ Quick Start Guide

Get your Intervention Tracking System running in 5 minutes!

## 🎯 What You Have

A complete knowledge graph-based system with:
- ✅ 5 demo participants with full data
- ✅ 70 intervention encounters
- ✅ Full navigation between all pages
- ✅ Analytics dashboard
- ✅ Ready for GitHub deployment

## 🚀 Three Ways to Run

### Option 1: Run Locally (Simplest)

**Mac/Linux:**
```bash
./run.sh
```

**Windows:**
```
run.bat
```

Then open: **http://localhost:5000**

That's it! The script automatically:
- Creates virtual environment
- Installs dependencies
- Loads demo data
- Starts the server

---

### Option 2: Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Generate demo data (if needed)
python demo_data_generator.py

# Run the app
python app.py
```

Open: **http://localhost:5000**

---

### Option 3: Deploy to GitHub

See **GITHUB_SETUP.md** for complete instructions.

**Quick version:**
1. Create GitHub repository
2. Upload all files
3. Create GitHub Codespace
4. Run `python app.py` in Codespace
5. Share the preview URL!

---

## 📍 Navigation Map

Once running, visit these pages:

### Main Dashboard
**http://localhost:5000/**
- Central hub with navigation to all features

### Core Functions
- **Add Participant**: `/participant/new`
- **Record Encounter**: `/encounter/new`  
- **Barrier Assessment**: `/assessment/new`

### View Data
- **All Participants**: `/participants`
- **All Encounters**: `/encounters`
- **Analytics**: `/analytics`

### Individual Tracking
- **Participant Progress**: `/participant/P001/progress`
- **Participant Encounters**: `/participant/P001/encounters`

Replace `P001` with P002, P003, P004, or P005 to see other participants.

---

## 🧪 Demo Data

The system includes 5 synthetic participants:

| ID | Scenario | Outcome |
|----|----------|---------|
| P001 | Good response | Significant improvement |
| P002 | Good response | Significant improvement |
| P003 | Poor response | Minimal change |
| P004 | Good response | Significant improvement |
| P005 | Delayed response | Slow then improved |

Each has:
- Baseline assessment
- 14 intervention encounters
- 3 follow-up assessments (30, 90, 180 days)

---

## 🎬 Recommended First Steps

1. **Start the system**
   ```bash
   ./run.sh    # or run.bat on Windows
   ```

2. **Explore the home page**
   - Visit http://localhost:5000
   - Click through the navigation cards

3. **View existing data**
   - Check out Participants page
   - Browse Encounters
   - Look at Analytics dashboard

4. **View individual progress**
   - Go to `/participant/P001/progress`
   - See barrier trajectories over time
   - Compare with P003 (poor responder)

5. **Try creating new data**
   - Add a new participant (P006)
   - Record an encounter
   - Conduct a baseline assessment

6. **Check analytics**
   - Visit `/analytics`
   - See service-wide statistics

---

## 🔄 Reset Demo Data

If you want fresh demo data:

```bash
# Delete existing data
rm data/demo_graph.ttl

# Regenerate
python demo_data_generator.py
```

---

## 📁 Project Structure

```
intervention-system/
├── app.py                    # ⭐ Main application - START HERE
├── run.sh / run.bat          # Easy startup scripts
├── requirements.txt          # Dependencies
├── README.md                 # Full documentation
├── GITHUB_SETUP.md          # GitHub deployment guide
├── 
├── Python Modules:
│   ├── ontology_core.py             # BCIO graph core
│   ├── barrier_assessment.py        # COM-B assessments
│   ├── demo_data_generator.py       # Create synthetic data
│   └── [other app modules]
│
├── templates/                # HTML pages
│   ├── index.html                   # Home page
│   ├── participant_progress.html   # Progress tracking
│   ├── analytics_dashboard.html    # Analytics
│   └── [8 more templates]
│
└── data/                     # RDF graph storage
    └── demo_graph.ttl               # Knowledge graph
```

---

## 🎯 Test Checklist

After starting, verify these work:

- [ ] Home page loads with navigation cards
- [ ] Can view 5 participants
- [ ] Can view 70 encounters
- [ ] Can create new participant (P006)
- [ ] Can record new encounter
- [ ] Can submit barrier assessment
- [ ] P001 progress page shows charts
- [ ] Analytics dashboard shows statistics
- [ ] All pages have working navigation back to home

---

## ⚠️ Troubleshooting

**Port 5000 already in use?**
```python
# Edit app.py, change last line to:
app.run(debug=True, port=5001)
```

**Dependencies not installing?**
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**No demo data?**
```bash
python demo_data_generator.py
```

**Page not loading?**
- Check terminal for errors
- Try http://127.0.0.1:5000 instead
- Clear browser cache

---

## 📧 Next Steps

1. ✅ Get it running locally
2. 📤 Upload to GitHub
3. 🌐 Deploy to cloud (optional)
4. 🎨 Customize for your organization
5. 📊 Start using with real data
6. 🔄 Iterate and improve

---

## 🆘 Need Help?

**Issue**: Can't run the scripts
- Make sure Python 3.8+ is installed
- Try running `python app.py` directly

**Issue**: Module not found errors
- Run: `pip install -r requirements.txt`
- Check you're in the right directory

**Issue**: Empty pages
- Check `data/demo_graph.ttl` exists
- Regenerate: `python demo_data_generator.py`

**Issue**: Want to deploy online
- See **GITHUB_SETUP.md** for detailed instructions
- Use GitHub Codespaces (easiest)
- Or deploy to Heroku/PythonAnywhere

---

**Ready?** Run `./run.sh` (or `run.bat` on Windows) and visit http://localhost:5000!

**Going to GitHub?** See **GITHUB_SETUP.md** for detailed deployment instructions.

🎉 **Enjoy your Intervention Tracking System!**
