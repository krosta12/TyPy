import ast
import sys
import inspect

def type_checked(func):
    def wrapper(*args, **kwargs):
        annotations = func.__annotations__
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        for name, value in bound_args.arguments.items():
            if name in annotations:
                expected = annotations[name]
                if not isinstance(value, expected):
                    raise TypeError(f"Аргумент '{name}' должен быть {expected}, получен {type(value)}")
        result = func(*args, **kwargs)
        if 'return' in annotations and annotations['return'] is not None:
            expected = annotations['return']
            if not isinstance(result, expected):
                raise TypeError(f"Функция должна возвращать {expected}, получен {type(result)}")
        return result
    return wrapper

def __type_check__(name, value, expected_type):
    if not isinstance(value, expected_type):
        raise TypeError(f"Переменная '{name}' должна быть {expected_type}, полченo {type(value)}")
    return value

class TypeScriptTransformer(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        has_annotation = (node.returns is not None) or any(arg.annotation is not None for arg in node.args.args)
        if has_annotation:
            decorator = ast.Name(id='type_checked', ctx=ast.Load())
            node.decorator_list.insert(0, decorator)
        self.generic_visit(node)
        return node

    def visit_AnnAssign(self, node):
        if node.value is not None:
            if isinstance(node.target, ast.Name):
                var_name = node.target.id
                check_call = ast.Call(
                    func=ast.Name(id='__type_check__', ctx=ast.Load()),
                    args=[
                        ast.Constant(value=var_name),
                        node.value,
                        node.annotation
                    ],
                    keywords=[]
                )
                new_node = ast.Assign(
                    targets=[node.target],
                    value=check_call
                )
                return ast.copy_location(new_node, node)
        return node

def main():
    if len(sys.argv) < 2:
        print("Использование: tpy_interpreter.py")
        sys.exit(1)
    file_path = sys.argv[1]
    if not file_path.endswith('.tpy'):
        print("Ошибка: файл должен иметь расширение .tpy")
        sys.exit(1)
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()
    tree = ast.parse(source, filename=file_path)
    transformer = TypeScriptTransformer()
    tree = transformer.visit(tree)
    ast.fix_missing_locations(tree)
    code = compile(tree, filename=file_path, mode='exec')
    env = {
        'type_checked': type_checked,
        '__type_check__': __type_check__,
        '__name__': '__main__'
    }
    exec(code, env)

if __name__ == '__main__':
    main()
