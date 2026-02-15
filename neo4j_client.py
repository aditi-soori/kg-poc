from neo4j import GraphDatabase

##create connection -> create nodes , relationships -> querying
class Neo4jClient:
    def __init__(self):
        ##init connection
        NEO4J_URI = "bolt://localhost:7687"
        NEO4J_USER = "neo4j"
        NEO4J_PASSWORD = "sample123"
        self.driver = GraphDatabase.driver(NEO4J_URI,auth=(NEO4J_USER, NEO4J_PASSWORD))
        print(f"**Connected to Neo4j**")
    
    def close(self):
        self.driver.close()
    
    def clear_database(self):
        ##match and delete all nodes + relationships
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
    
    def create_indexes(self):
        ##faster lookup
        #index file nodes by name, path
        #index function, class, variable nodes by name
        with self.driver.session() as session:
            session.run("CREATE INDEX file_name IF NOT EXISTS FOR (f:File) ON (f.name)")
            session.run("CREATE INDEX file_path IF NOT EXISTS FOR (f:File) ON (f.path)")
            session.run("CREATE INDEX function_name IF NOT EXISTS FOR (func:Function) ON (func.name)")
            session.run("CREATE INDEX class_name IF NOT EXISTS FOR (c:Class) ON (c.name)")
            session.run("CREATE INDEX variable_name IF NOT EXISTS FOR (v:Variable) ON (v.name)")
    
    def create_file_nodes(self, files):
        #start session ,loop through each file
        #create/update file node
        with self.driver.session() as session:
            #create file node w file path
            for file in files:
                session.run(
                    """
                    MERGE (f:File {path: $path})
                    SET f.name = $name
                    """,
                    path=file['path'],#filepath
                    name=file['name']#filename
                )
    
    def create_function_nodes(self, functions):
        ##create function node 
        ##link function to file
        ##link function to params
        with self.driver.session() as session:
            for func in functions:
                ##crete functn node on name n file path
                session.run(
                    """
                    MERGE (func:Function {name: $name, file_path: $file_path})
                    SET func.line_number = $line_number
                    """,
                    name=func['name'],#function name
                    file_path=func['file_path'],#function in which file
                    line_number=func['line_number'] #function line no.
                )
                ##link functn to file that has it 
                #find file node -> find functn node -> file CONTAINS func
                session.run(
                    """
                    MATCH (f:File {path: $file_path})
                    MATCH (func:Function {name: $name, file_path: $file_path})
                    MERGE (f)-[:CONTAINS]->(func)
                    """,
                    file_path=func['file_path'],
                    name=func['name']
                )
                
                #find functn node -> find/create var node -> func DEFINES param
                for param in func.get('parameters', []):
                    session.run(
                        """
                        MATCH (func:Function {name: $func_name, file_path: $file_path})
                        MERGE (v:Variable {name: $param, file_path: $file_path})
                        MERGE (func)-[:DEFINES]->(v)
                        """,
                        func_name=func['name'],
                        file_path=func['file_path'],
                        param=param
                    )
    
    def create_class_nodes(self, classes):
        #create class node, link to file
        with self.driver.session() as session:
            #class node on name and file path
            for c in classes:
                session.run(
                    """
                    MERGE (c:Class {name: $name, file_path: $file_path})
                    SET c.line_number = $line_number
                    """,
                    name=c['name'],
                    file_path=c['file_path'],
                    line_number=c['line_number']
                )
                #find file -> find class -> file CONTAINS class
                session.run(
                    """
                    MATCH (f:File {path: $file_path})
                    MATCH (c:Class {name: $name, file_path: $file_path})
                    MERGE (f)-[:CONTAINS]->(c)
                    """,
                    file_path=c['file_path'],
                    name=c['name']
                )
    
    def create_call_relationships(self, calls):
        #loop thru functn calls and link caller to callee by name.caller CALLS calllee
        with self.driver.session() as session:
            for call in calls:
                session.run(
                    """
                    MATCH (caller:Function {name: $caller})
                    MATCH (callee:Function {name: $callee})
                    MERGE (caller)-[:CALLS]->(callee)
                    """,
                    caller=call['caller'],
                    callee=call['callee']
                )
    
    def create_import_nodes(self, imports):
        ##create import node on module name
        with self.driver.session() as session:
            for imp in imports:
                session.run(
                    """
                    MERGE (i:Import {module_name: $module_name})
                    SET i.import_type = $import_type
                    """,
                    module_name=imp['module_name'],
                    import_type=imp['import_type']
                )
                #find file with import -> find import node -> file IMPORTS import
                session.run(
                    """
                    MATCH (f:File {path: $file_path})
                    MATCH (i:Import {module_name: $module_name})
                    MERGE (f)-[:IMPORTS]->(i)
                    """,
                    file_path=imp['file_path'],
                    module_name=imp['module_name']
                )
        
    def create_variable_nodes(self, variables):
        #create var node on name and file path -- same var in diff files
        with self.driver.session() as session:
            for var in variables:
                session.run(
                    """
                    MERGE (v:Variable {name: $name, file_path: $file_path})
                    SET v.line_number = $line_number
                    """,
                    name=var['name'],
                    file_path=var['file_path'],
                    line_number=var['line_number']
                )
                
                # find file -> find var node -> file CONTAINS var
                session.run(
                    """
                    MATCH (f:File {path: $file_path})
                    MATCH (v:Variable {name: $name, file_path: $file_path})
                    MERGE (f)-[:CONTAINS]->(v)
                    """,
                    file_path=var['file_path'],
                    name=var['name']
                )
        
    def build_graph(self, parsed_data):
        #create nodes + relationships
        self.create_file_nodes(parsed_data['files'])
        self.create_function_nodes(parsed_data['functions'])
        self.create_class_nodes(parsed_data['classes'])
        self.create_variable_nodes(parsed_data['variables'])
        self.create_import_nodes(parsed_data['imports'])
        self.create_call_relationships(parsed_data['calls'])
    