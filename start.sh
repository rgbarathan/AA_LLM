#!/bin/bash

echo "=================================================="
echo "Telecom Architecture Advisor - Quick Start"
echo "=================================================="
echo ""
echo "Choose an option:"
echo "1. Run Interactive CLI (Enhanced Features)"
echo "2. Run Web Interface (Streamlit)"
echo "3. Run Basic RAG Demo"
echo "4. Install Dependencies"
echo "5. Exit"
echo ""
read -p "Enter choice [1-5]: " choice

case $choice in
    1)
        echo "Starting Interactive CLI..."
        python3 telecom_advisor_enhanced.py
        ;;
    2)
        echo "Starting Web Interface..."
        echo "Opening browser at http://localhost:8501"
        streamlit run streamlit_app.py
        ;;
    3)
        echo "Running Basic RAG Demo..."
        python3 telecom_advisor_rag.py
        ;;
    4)
        echo "Installing dependencies..."
        pip install -r requirements.txt
        echo "Installation complete!"
        ;;
    5)
        echo "Goodbye!"
        exit 0
        ;;
    *)
        echo "Invalid choice. Please run again."
        exit 1
        ;;
esac
