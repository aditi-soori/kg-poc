import sys
import os
from code_parser import CodeParser
from neo4j_client import Neo4jClient

def main():
    #get codebase path 
    codebase_path = sys.argv[1]
    #parse codebase
    print("\nParsing codebase")
    parser = CodeParser()
    parsed_data = parser.parse_codebase(codebase_path)

    print("\nNumber of")
    print("Files:", len(parsed_data['files']))
    print("Functions:", len(parsed_data['functions']))
    print("Classes:", len(parsed_data['classes']))
    print("Variables:", len(parsed_data['variables']))
    print("Imports:", len(parsed_data['imports']))
    print("Function Calls:", len(parsed_data['calls']))

    #connect to Neo4j
    neo4j = Neo4jClient()

    #build kg
    print("Building knowledge graph...")
    neo4j.create_indexes()
    neo4j.build_graph(parsed_data)
    neo4j.close()

if __name__ == "__main__":
    main()
