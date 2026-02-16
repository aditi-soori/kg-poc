1. Read each .py file 
2. Parse with tree sitter -> Return AST 
3. Walk AST ,Get AST nodes and relationships
    ->fetch_functions
        -func_name
        -line no.
        -param
        -file_path
        -parent class
    ->fetch_classes
        -class_name
        -line no.
        -file_path
        -parent class
    ->fetch_variables
        -var_name
        -line no.
        -file_path
    ->fetch_function_calls
        -caller_name
        -callee_name
        -file_path
    ->fetch_imports
        -module_name
        -file_path
        -import_type
3. Connect to neo4j
4. Create node and relationships
5. Query graph
