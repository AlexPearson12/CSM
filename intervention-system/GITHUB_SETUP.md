# 🚀 GitHub Setup Guide

Complete guide to setting up and launching your Intervention Tracking System on GitHub.

## Option 1: Deploy on GitHub (Recommended for Sharing)

### Step 1: Create GitHub Repository

1. Go to [GitHub](https://github.com) and sign in (or create an account)
2. Click the **"+"** icon in top right → **"New repository"**
3. Repository settings:
   - **Name**: `intervention-tracking-system` (or your preferred name)
   - **Description**: "Knowledge graph-based behavioral intervention tracking"
   - **Visibility**: Public (so others can access it)
   - ✓ Check "Add a README file" (optional, we already have one)
4. Click **"Create repository"**

### Step 2: Upload Your Files

#### Method A: Using GitHub Web Interface (Easiest)

1. In your new repository, click **"uploading an existing file"** or **"Add file" → "Upload files"**
2. Drag and drop ALL these files/folders:
   ```
   app.py
   ontology_core.py
   barrier_assessment.py
   demo_data_generator.py
   encounter_app.py
   participant_intake_app.py
   barrier_assessment_app.py
   quick_start.py
   requirements.txt
   README.md
   .gitignore
   templates/ (entire folder)
   data/ (entire folder)
   ```
3. Scroll down and click **"Commit changes"**

#### Method B: Using Git Command Line

```bash
# Navigate to your project folder
cd /path/to/intervention-system

# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Intervention tracking system"

# Connect to your GitHub repo (replace with your URL)
git remote add origin https://github.com/yourusername/intervention-tracking-system.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 3: Enable GitHub Codespaces (For Running the App)

**Note**: This is for running the actual Flask app. GitHub Pages doesn't support Python backends.

1. In your repository, click the green **"Code"** button
2. Click **"Codespaces"** tab
3. Click **"Create codespace on main"**
4. Wait for the environment to load (this creates a cloud-based VS Code environment)

### Step 4: Run Your App in Codespaces

Once Codespaces loads:

1. **Open terminal** in Codespaces (Terminal → New Terminal)

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app**:
   ```bash
   python app.py
   ```

4. **Access your app**: Codespaces will show a popup saying "Your application running on port 5000 is available"
   - Click **"Open in Browser"**
   - You'll get a URL like: `https://username-reponame-xxxx.githubpreview.dev`

5. **Share the link**: Copy this URL and share it with anyone you want to access your system!

---

## Option 2: Run Locally

If you just want to run it on your computer:

### Prerequisites
- Python 3.8 or higher
- pip (comes with Python)

### Setup

1. **Download/Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/intervention-tracking-system.git
   cd intervention-tracking-system
   ```

2. **Create virtual environment** (recommended):
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On Mac/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Generate demo data** (optional):
   ```bash
   python demo_data_generator.py
   ```

5. **Run the application**:
   ```bash
   python app.py
   ```

6. **Open your browser**:
   ```
   http://localhost:5000
   ```

---

## Option 3: Deploy on a Cloud Platform

### Heroku

1. **Create Heroku account** at [heroku.com](https://heroku.com)

2. **Install Heroku CLI**

3. **Create `Procfile`**:
   ```
   web: python app.py
   ```

4. **Deploy**:
   ```bash
   heroku create your-app-name
   git push heroku main
   heroku open
   ```

### PythonAnywhere

1. **Create account** at [pythonanywhere.com](https://pythonanywhere.com) (free tier available)

2. **Upload files** via their web interface

3. **Set up web app**:
   - Choose Flask
   - Point to your `app.py`
   - Install requirements
   - Reload

4. **Access** at: `yourusername.pythonanywhere.com`

---

## 🎯 Quick Test Checklist

After deployment, test these pages:

- [ ] **Home** - Shows main navigation dashboard
- [ ] **Add Participant** - Form works, creates P006
- [ ] **View Participants** - Shows P001-P005 from demo data
- [ ] **View Encounters** - Shows 70 demo encounters
- [ ] **Record Encounter** - Can create new encounter
- [ ] **Barrier Assessment** - Form works, can submit assessment
- [ ] **Participant Progress** - Shows charts for P001
- [ ] **Analytics Dashboard** - Shows service-wide statistics

---

## 🔧 Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt
```

### Port 5000 already in use
Change port in `app.py`:
```python
app.run(debug=True, port=5001)  # Change to 5001 or any available port
```

### No demo data showing
```bash
python demo_data_generator.py
```

### RDF graph errors
Delete `data/demo_graph.ttl` and regenerate:
```bash
rm data/demo_graph.ttl
python demo_data_generator.py
```

---

## 📱 Sharing Your System

### Option A: GitHub Codespaces (Best for collaboration)
1. Create Codespace as described above
2. Share the preview URL (valid while Codespace is running)
3. Others can also create their own Codespace from your repo

### Option B: Deploy to Cloud
1. Use Heroku/PythonAnywhere
2. Get permanent URL
3. Share URL - no setup needed for users

### Option C: Share Repository
1. Share GitHub repo URL
2. Users clone and run locally
3. Requires technical setup on their end

---

## 🎨 Customization

### Change Branding
Edit `templates/index.html`:
- Title: Line 5
- Header: Line 51
- Colors: Lines 11-13 (CSS gradient)

### Add Logo
1. Create `static/` folder
2. Add `logo.png`
3. Reference in templates: `<img src="{{ url_for('static', filename='logo.png') }}">`

### Modify Navigation
Edit `templates/index.html` nav-grid sections (lines 62-113)

---

## 📊 Next Steps

1. ✅ Upload to GitHub
2. ✅ Create Codespace or deploy to cloud
3. ✅ Test all pages
4. 📧 Share with team
5. 📝 Customize for your organization
6. 🔄 Iterate based on feedback

---

**Need Help?** Create an issue on your GitHub repository or contact [your-email]

**Repository Template**: This can serve as a template - click "Use this template" on GitHub to create new instances for different projects!
