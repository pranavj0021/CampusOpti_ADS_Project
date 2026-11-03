#!/bin/bash
# Start Flask Backend in background on internal port 5000
PORT=5000 python backend/app.py &

# Wait 2 seconds for backend to start
sleep 2

# Start Streamlit Frontend bound to Render's public $PORT
streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0

