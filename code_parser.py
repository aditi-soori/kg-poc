import os
from tree_sitter_languages import get_language, get_parser

class CodeParser:
    def __init__(self) :
        self.PY_LANGUAGE = get_language('python')
        self.parser = get_parser('python')
    
    def parse_file(self, file_path):
        ##parse py file -> return AST
        #read file in binary
        with open(file_path, 'rb') as f:
            source_code = f.read()
        #convert code to syntax tree
        tree = self.parser.parse(source_code) 
        return tree, source_code
    
    ##extract entities 1. functions 2. classes 3. variables

    def fetch_functions(self, tree, source_code, file_path):
        ##get all functions from ast
        functions = []

        def traverse(node, parent_class=None):
            ##if node is a function -> get function name -> extract params,func_name..
            if node.type == "function_definition":
                name_node = node.child_by_field_name('name') ##get function name
                ##convert byte positions into func name string
                if name_node:
                    func_name = source_code[name_node.start_byte:name_node.end_byte].decode('utf-8')
                    params = []
                    ## get params from function -> loop throught params -> get identifiers
                    params_node = node.child_by_field_name('parameters') ##get params
                    if params_node:
                        for child  in params_node.children:
                            if child.type == 'identifier':
                                param_name = source_code[child.start_byte:child.end_byte].decode('utf-8') ##convert to string
                                params.append(param_name)
                    
                    functions.append({
                        'name': func_name,
                        'line_number': node.start_point[0] + 1,#line numbers start at 0
                        'file_path': file_path,
                        'parameters': params,
                        'parent_class': parent_class ##which class func belongs to
                    })
            
            ##if class, pass name to children
            elif node.type == "class_definition":
                name_node = node.child_by_field_name('name')
                if name_node:
                    class_name = source_code[name_node.start_byte:name_node.end_byte].decode('utf-8')
                    #traverse children witht this class name
                    for child in node.children:
                        traverse(child, parent_class=class_name)
                    return 
            
            for child in node.children:
                traverse(child, parent_class)
        traverse(tree.root_node) ##top of ast->file
        return functions

    def fetch_classes(self, tree, source_code, file_path):
        classes = []
        ##parent class in case of nested classes 
        def traverse(node, parent_class=None):
            if node.type == "class_definition":
                name_node = node.child_by_field_name('name')#get name of class 
                if name_node:
                    class_name = source_code[name_node.start_byte:name_node.end_byte].decode('utf-8')

                    classes.append({
                        'name': class_name,
                        'line_number': node.start_point[0] + 1,#line numbers start at 0
                        'file_path': file_path,
                        'parent_class': parent_class
                    })
            
            for child in node.children:
                traverse(child,parent_class)
        traverse(tree.root_node)
        return classes
    
    def fetch_variables(self, tree, source_code, file_path):
        ##handles only top level variables
        ##neeed to work on extracting tuples, attributes, type annotations
        variables=[]
        def traverse(node, depth=0):
            ##check if cur__node is of type assignment and depth=1 to ensure only top level vars and should be direclty  under module
            if node.type == 'assignment' and depth == 1:
                left_node = node.child_by_field_name('left')
                if left_node and left_node.type == 'identifier':
                    var_name = source_code[left_node.start_byte:left_node.end_byte].decode('utf-8')
                    variables.append({
                        'name': var_name,
                        'line_number': node.start_point[0] + 1,
                        'file_path': file_path
                    })
            
            for child in node.children:
                traverse(child, depth +1)
        
        traverse(tree.root_node)
        return variables

    ##extract relationships 1.calls 2.imports 3.inheritance

    def fetch_function_calls(self, tree, source_code, file_path):
        ##functions -> nodes ; calls-> edges
        calls=[]
        ##get name of function we are currently inside
        def traverse(node, in_function=None):
            if node.type == 'function_definition':
                name_node = node.child_by_field_name('name')
                if name_node:
                    func_name = source_code[name_node.start_byte:name_node.end_byte].decode('utf-8')
                ##traverse function body pass funcname return so that no double traversa,
                    for child in node.children:
                        traverse(child, in_function=func_name)
                return 
            ##if curr node is a call
            if node.type == 'call':
                called_func = None 
                function_node = node.child_by_field_name('function')
                #only if we are in a function store relation
                if function_node and in_function:
                    if function_node.type == 'identifier':
                        called_func = source_code[function_node.start_byte:function_node.end_byte].decode('utf-8')
                
                    ##handle method calks
                    elif function_node.type == 'attribute':
                        attr_node = function_node.child_by_field_name('attribute')
                        if attr_node:
                            called_func = source_code[attr_node.start_byte:attr_node.end_byte].decode('utf-8')

                    if called_func:
                        calls.append({
                            'caller': in_function,
                            'callee': called_func,
                            'file_path': file_path
                        })

            for child in node.children:
                traverse(child, in_function)

        traverse(tree.root_node)
        return calls

    def fetch_imports(self, tree, source_code, file_path):
        ##extract import relationships
        imports = []
        
        def traverse(node):
            ##handle import for module name, dotted names like os.join
            if node.type == 'import_statement':
                for child in node.children:
                    if child.type == 'dotted_name':
                        module_name = source_code[child.start_byte:child.end_byte].decode('utf-8')
                        imports.append({
                            'module_name': module_name,
                            'file_path': file_path,
                            'import_type': 'import'
                        })
            ##from module import x
            elif node.type == 'import_from_statement':
                module_node = node.child_by_field_name('module_name')
                if module_node:
                    module_name = source_code[module_node.start_byte:module_node.end_byte].decode('utf-8')
                    imports.append({
                        'module_name': module_name,
                        'file_path': file_path,
                        'import_type': 'from_import'
                    })
            
            for child in node.children:
                traverse(child)
        
        traverse(tree.root_node)
        return imports
 
    def parse_codebase(self, directory_path):
        #parse through codebase, get node-relationships
        all_data = {
            'functions': [],
            'classes': [],
            'calls': [],
            'imports': [],
            'variables': [],
            'files': []
        }
        
        for root, dirs, files in os.walk(directory_path):
            dirs[:] = [d for d in dirs if d not in ['venv','.git', 'node_modules', 'dist', 'build']]
            
            for file in files:
                if any(file.endswith(ext) for ext in ['.py']):
                    file_path = os.path.join(root, file)
                    ##parse file ,get ast
                    try:
                        print(f"Parsing: {file_path}")
                        tree, source_code = self.parse_file(file_path)
                        
                        #extract 
                        all_data['functions'].extend(self.fetch_functions(tree, source_code, file_path))
                        all_data['classes'].extend(self.fetch_classes(tree, source_code, file_path))
                        all_data['calls'].extend(self.fetch_function_calls(tree, source_code, file_path))
                        all_data['imports'].extend(self.fetch_imports(tree, source_code, file_path))
                        all_data['variables'].extend(self.fetch_variables(tree, source_code, file_path))
                        
                        #store file path n name
                        all_data['files'].append({
                            'path': file_path,
                            'name': file
                        })
                        
                    except Exception as e:
                        print(f"Error while parsing {file_path}: {e}")
        
        return all_data
