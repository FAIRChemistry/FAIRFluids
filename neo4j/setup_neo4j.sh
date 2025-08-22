#!/bin/bash

echo "🗄️  Setting up Neo4j for FAIRFluids Knowledge Graph"
echo "=================================================="

# Check if Docker is running
if ! sudo docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Stop and remove existing Neo4j container if it exists
echo "🔄 Stopping existing Neo4j container..."
sudo docker stop fairfluids-neo4j 2>/dev/null || true
sudo docker rm fairfluids-neo4j 2>/dev/null || true

# Create Neo4j container
echo "🚀 Starting Neo4j container..."
sudo docker run -d \
    --name fairfluids-neo4j \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/password \
    -e NEO4J_PLUGINS='["apoc"]' \
    -e NEO4J_dbms_security_procedures_unrestricted=apoc.* \
    neo4j:5.15

echo "⏳ Waiting for Neo4j to start..."
sleep 30

# Check if Neo4j is ready
echo "🔍 Checking Neo4j status..."
if curl -s http://localhost:7474 > /dev/null; then
    echo "✅ Neo4j is running!"
    echo ""
    echo "🌐 Neo4j Browser: http://localhost:7474"
    echo "🔑 Username: neo4j"
    echo "🔑 Password: password"
    echo ""
    echo "📊 Connection details for Python script:"
    echo "   URI: bolt://localhost:7687"
    echo "   Username: neo4j"
    echo "   Password: password"
    echo ""
    echo "💡 You can now run:"
    echo "   python create_neo4j_graph.py --clear --queries"
else
    echo "❌ Neo4j failed to start. Please check Docker logs:"
    echo "   docker logs fairfluids-neo4j"
fi
