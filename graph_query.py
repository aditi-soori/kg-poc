from neo4j_client import Neo4jClient

class GraphQuery:
    def __init__(self):
        self.neo4j = Neo4jClient()
    
    def query_functions_in_file(self, filename):
        ##find total no.of functions in file
        with self.neo4j.driver.session() as session:
            result = session.run(
                """
                MATCH (f:File {name: $filename})-[:CONTAINS]->(func:Function)
                RETURN func.name as function_name, func.line_number as line
                """,
                filename=filename
            )
            
            functions = [(record['function_name'], record['line']) for record in result]
            if functions:
                for func_name, line in functions:
                    print(f"#{func_name} (line {line})")
                print(f"\nTotal: {len(functions)} functions")
            else:
                print(f"No functions found")  
            return functions
    
    def query_files_with_variable(self, var_name):
        ##Find files where var x is used 
        with self.neo4j.driver.session() as session:
            result = session.run(
                """
                MATCH (f:File)-[:CONTAINS]->(v:Variable {name: $var_name})
                RETURN DISTINCT f.name as file_name, f.path as file_path
                """,
                var_name=var_name
            )
            files = [(record['file_name'], record['file_path']) for record in result]
            if files:
                for file_name, file_path in files:
                    print(f"File name:{file_name}")
                    print(f"File path:({file_path})")
            else:
                print(f"Variable '{var_name}' not found")
            
            return files
    
    def query_function_callers(self, func_name):
       ##which function calls function x 
        with self.neo4j.driver.session() as session:
            result = session.run(
                """
                MATCH (caller:Function)-[:CALLS]->(callee:Function {name: $func_name})
                RETURN caller.name as caller_name, caller.file_path as caller_file
                """,
                func_name=func_name
            ) 
            callers = [(record['caller_name'], record['caller_file']) for record in result]

            if callers:
                for caller_name, caller_file in callers:
                    print(f"{caller_name}")
                    print(f"(in {caller_file})")
            else:
                print(f"No callers found")
            
            return callers
    
    def query_function_calls(self, func_name):
        #which function does x call
        with self.neo4j.driver.session() as session:
            result = session.run(
                """
                MATCH (caller:Function {name: $func_name})-[:CALLS]->(callee:Function)
                RETURN callee.name as callee_name, callee.file_path as callee_file
                """,
                func_name=func_name
            )
            
            callees = [(record['callee_name'], record['callee_file']) for record in result]
            if callees:
                for callee_name, callee_file in callees:
                    print(f"{callee_name}")
                    print(f"(in {callee_file})")
            else:
                print(f"function doesn't call any other functions")
            return callees
    
    def query_class_methods(self, class_name):
        ##what methods are in class x
        with self.neo4j.driver.session() as session:
            result = session.run(
                """
                MATCH (c:Class {name: $class_name})-[:HAS_METHOD]->(m:Function)
                RETURN m.name as method_name, m.line_number as line
                """,
                class_name=class_name
            )           
            methods = [(record['method_name'], record['line']) for record in result]
            if methods:
                for method_name, line in methods:
                    print(f"{method_name} (line {line})")
            else:
                print(f"no methods found")
            return methods
    
    def query_file_imports(self, filename):
        ##what does file x import
        with self.neo4j.driver.session() as session:
            result = session.run(
                """
                MATCH (f:File {name: $filename})-[:IMPORTS]->(i:Import)
                RETURN i.module_name as module, i.import_type as import_type
                """,
                filename=filename
            )            
            imports = [(record['module'], record['import_type']) for record in result]
            if imports:
                for module, import_type in imports:
                    print(f"   - {module} ({import_type})")
            else:
                print(f"No imports found")
            
            return imports
    
    def query_all_files(self):
        ##list of all files
        with self.neo4j.driver.session() as session:
            result = session.run(
                """
                MATCH (f:File)
                RETURN f.name as name, f.path as path
                ORDER BY f.name
                """
            )
            
            files = [(record['name'], record['path']) for record in result]
            for name in files:
                print(f"{name}")
            print(f"\nTotal: {len(files)} files")
            
            return files
    
    def query_all_functions(self):
        """List all functions in the knowledge graph"""
        with self.neo4j.driver.session() as session:
            result = session.run(
                """
                MATCH (func:Function)
                RETURN func.name as name, func.file_path as file
                ORDER BY func.name
                """
            )
            
            functions = [(record['name'], record['file']) for record in result]
            
            print(f"\n⚙️  All functions:")
            for name, file in functions:
                print(f"   - {name} (in {file})")
            print(f"\nTotal: {len(functions)} functions")
            
            return functions
    
    def custom_query(self, cypher_query):
        with self.neo4j.driver.session() as session:
            result = session.run(cypher_query)
            records = [dict(record) for record in result]
            for record in records:
                print(f"{record}")
            print(f"\nTotal: {len(records)} results")
            
            return records
    
    def close(self):
        self.neo4j.close()

def query():
    queryer = GraphQuery() 
    print("==KG QUERY==")
    while True:
        print("1.Find all functions in the file")
        print("2.Find files that have the variable")
        print("3.Which function/method calls function/method x ")
        print("4.Which function/method does x call")
        print("5.List of all methods in the class")
        print("6.List of all imports in file")
        print("7.List all files")
        print("8.List all functions")
        print("9.Custom Cypher query")
        print("0.Exit")
        
        choice = input("\noption: ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            filename = input("Enter file: ").strip()
            queryer.query_functions_in_file(filename)
        elif choice == '2':
            var_name = input("Enter variable: ").strip()
            queryer.query_files_with_variable(var_name)
        elif choice == '3':
            func_name = input("Enter function: ").strip()
            queryer.query_function_callers(func_name)
        elif choice == '4':
            func_name = input("Enter function: ").strip()
            queryer.query_function_calls(func_name)
        elif choice == '5':
            class_name = input("Enter class: ").strip()
            queryer.query_class_methods(class_name)
        elif choice == '6':
            filename = input("Enter file: ").strip()
            queryer.query_file_imports(filename)
        elif choice == '7':
            queryer.query_all_files()
        elif choice == '8':
            queryer.query_all_functions()
        elif choice == '9':
            print("\nEnter Cypher query (end with semicolon):")
            query = input().strip()
            try:
                queryer.custom_query(query)
            except Exception as e:
                print(f"Query error: {e}")
        else:
            print("Invalid option")
    
    queryer.close()

if __name__ == "__main__":
    query()