#!/bin/bash
echo "=========================================="
echo "  Intervention Tracking System"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Check if demo data exists
if [ ! -f "data/demo_graph.ttl" ]; then
    echo ""
    echo "No demo data found. Generating..."
    python demo_data_generator.py
fi

# Run the app
echo ""
echo "=========================================="
echo "  Starting server..."
echo "=========================================="
echo ""
echo "📊 Intervention Tracking System"
echo ""
echo "🌐 Open your browser and visit:"
echo "   http://localhost:5000"
echo ""
echo "📚 Available pages:"
echo "   • Home: http://localhost:5000/"
echo "   • Participants: http://localhost:5000/participants"
echo "   • Encounters: http://localhost:5000/encounters"
echo "   • Analytics: http://localhost:5000/analytics"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

python app.py
