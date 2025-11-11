#!/usr/bin/env python3
"""
Quick Start Setup Script
Automates demo data generation and app launch
"""

import subprocess
import sys
import time
from pathlib import Path

def print_header(text):
    """Print formatted section header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def run_command(command, description):
    """Run a shell command with status updates"""
    print(f"[...] {description}...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"[OK] {description} - Success!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[X] {description} - Failed!")
        print(f"   Error: {e.stderr}")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    print_header("Checking Dependencies")
    
    required = ['flask', 'rdflib']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"[OK] {package} - installed")
        except ImportError:
            print(f"[X] {package} - missing")
            missing.append(package)
    
    if missing:
        print(f"\n[!] Missing packages: {', '.join(missing)}")
        print("   Installing...")
        return run_command(
            f"pip install {' '.join(missing)}",
            "Installing dependencies"
        )
    
    return True

def generate_demo_data():
    """Generate synthetic demonstration data"""
    print_header("Generating Demo Data")
    
    if Path('data/demo_graph.ttl').exists():
        print("[!] Demo data already exists")
        response = input("   Regenerate? (y/N): ").lower()
        if response != 'y':
            print("   Skipping data generation")
            return True
    
    return run_command(
        "python demo_data_generator.py",
        "Generating synthetic participants and assessments"
    )

def launch_app():
    """Launch the barrier assessment app"""
    print_header("Launching Application")
    
    print(">> Starting barrier assessment app on http://localhost:5001")
    print("\n>> Available Dashboards:")
    print("   * http://localhost:5001/participant/P001/progress")
    print("   * http://localhost:5001/analytics/dashboard")
    print("   * http://localhost:5001/assessment/new")
    print("\n>> Press Ctrl+C to stop\n")
    
    time.sleep(2)
    
    try:
        subprocess.run(
            ["python", "barrier_assessment_app.py"],
            check=True
        )
    except KeyboardInterrupt:
        print("\n\n[!] Shutting down...")
        print("   App stopped successfully")
    except Exception as e:
        print(f"\n[X] Error running app: {e}")
        return False
    
    return True

def main():
    """Main setup workflow"""
    print("""
================================================================
                                                              
     Barrier Assessment System - Quick Start Setup           
     ----------------------------------------------------         
     Extends your existing BCIO prototype with:               
       * COM-B barrier assessment                             
       * Outcome tracking & change calculation                
       * Individual progress dashboards                       
       * Service-wide analytics                               
                                                              
================================================================
    """)
    
    # Step 1: Check dependencies
    if not check_dependencies():
        print("\n[X] Setup failed at dependency check")
        print("   Try running: pip install flask rdflib")
        return False
    
    # Step 2: Generate data
    if not generate_demo_data():
        print("\n[X] Setup failed at data generation")
        return False
    
    # Step 3: Launch app
    print_header("Ready to Launch")
    print("Setup complete! Ready to start the application.")
    
    response = input("\nLaunch app now? (Y/n): ").lower()
    if response in ['', 'y', 'yes']:
        launch_app()
    else:
        print("\n[OK] Setup complete!")
        print("\nTo start the app manually, run:")
        print("   python barrier_assessment_app.py")
        print("\nThen visit:")
        print("   http://localhost:5001/participant/P001/progress")
        print("   http://localhost:5001/analytics/dashboard")
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[!] Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[X] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
