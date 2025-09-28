#!/usr/bin/env python3
"""
Quick Neo4j database analysis script
Run this to check your 708 nodes and relationships
"""

from neo4j import GraphDatabase
import json

# Neo4j Aura connection details
NEO4J_URI = "neo4j+s://fb98514e.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "uHdujIiUOKRvStfpmfDA7W3bodJUjfoLxD2OlaXPCSg"

def run_analysis():
    """Run analysis queries on the Neo4j database"""
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        with driver.session() as session:
            print("🔍 ANALYZING YOUR NEO4J DATABASE")
            print("=" * 50)
            
            # 1. Check node distribution
            print("\n📊 NODE DISTRIBUTION:")
            result = session.run("""
                MATCH (n) 
                RETURN DISTINCT labels(n) as NodeType, count(n) as Count
                ORDER BY Count DESC
            """)
            
            total_nodes = 0
            for record in result:
                node_type = record["NodeType"]
                count = record["Count"]
                total_nodes += count
                print(f"  {node_type}: {count:,} nodes")
            
            print(f"\n  TOTAL NODES: {total_nodes:,}")
            
            # 2. Check relationships
            print("\n🔗 RELATIONSHIP DISTRIBUTION:")
            result = session.run("""
                MATCH ()-[r]->() 
                RETURN type(r) as RelationshipType, count(r) as Count
                ORDER BY Count DESC
            """)
            
            total_rels = 0
            for record in result:
                rel_type = record["RelationshipType"]
                count = record["Count"]
                total_rels += count
                print(f"  {rel_type}: {count:,} relationships")
            
            print(f"\n  TOTAL RELATIONSHIPS: {total_rels:,}")
            
            # 3. Sample data structure
            print("\n📋 SAMPLE NODES (First 5):")
            result = session.run("MATCH (n) RETURN n LIMIT 5")
            
            for i, record in enumerate(result, 1):
                node = record["n"]
                labels = list(node.labels)
                props = dict(node.items())
                print(f"\n  Node {i}:")
                print(f"    Labels: {labels}")
                print(f"    Properties: {list(props.keys())}")
                # Show first few characters of each property
                for key, value in props.items():
                    if isinstance(value, str) and len(value) > 50:
                        print(f"      {key}: {value[:50]}...")
                    else:
                        print(f"      {key}: {value}")
            
            # 4. Check connectivity
            print("\n🌐 CONNECTIVITY ANALYSIS:")
            result = session.run("""
                MATCH (n)
                WHERE size((n)--()) > 0
                RETURN labels(n) as NodeType, 
                       avg(size((n)--())) as AvgConnections,
                       max(size((n)--())) as MaxConnections,
                       count(n) as ConnectedNodes
                ORDER BY AvgConnections DESC
            """)
            
            for record in result:
                node_type = record["NodeType"]
                avg_conn = record["AvgConnections"]
                max_conn = record["MaxConnections"]
                connected_count = record["ConnectedNodes"]
                print(f"  {node_type}: {connected_count} nodes, avg {avg_conn:.1f} connections, max {max_conn}")
            
    except Exception as e:
        print(f"❌ Error connecting to Neo4j: {e}")
        print("\n💡 Make sure:")
        print("  1. Neo4j is running")
        print("  2. Update the connection details in this script")
        print("  3. Check your username/password")
        
    finally:
        driver.close()

if __name__ == "__main__":
    print("🚀 Starting Neo4j Database Analysis...")
    run_analysis()
    print("\n✅ Analysis complete!")