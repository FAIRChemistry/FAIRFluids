#!/bin/bash

# FAIRFluids Web Interface Startup Script

echo "Starting FAIRFluids Web Interface"
echo "=================================="
# Check if Neo4j is running
echo "Checking Neo4j connection..."
python -c "
from neo4j import GraphDatabase
try:
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))
    with driver.session() as session:
        result = session.run('MATCH (n) RETURN count(n) as total')
        count = result.single()['total']
        print(f'Neo4j connected - {count} nodes in database')
    driver.close()
except Exception as e:
    print(f'Neo4j connection failed: {e}')
    print('Please start Neo4j first: cd ../neo4j && ./setup_neo4j.sh')
    exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

# Check if requirements are installed
echo "Checking dependencies..."
python -c "
import flask, neo4j, plotly, pandas, numpy
print('All dependencies available')
" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the Flask application
echo "Starting web server..."
echo "   URL: http://localhost:5000"
echo "   Press Ctrl+C to stop"
echo ""

# Change to the test_website directory before running app.py
cd "$(dirname "$0")"
python app.py


