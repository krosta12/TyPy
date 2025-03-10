import ast
import sys
import re
import inspect
from enum import Enum
from typing import Optional

def __assert_type__(value, expected_type):
    if not isinstance(value, expected_type):
        raise TypeError(f"Ошибка приведения: знагчение {value} не типа {expected_type}")
    return value

def __type_check__(name, value, expected_type):
    if not isinstance(value, expected_type):
        raise TypeError(f"Переменная '{name}' должна быть {expected_type}, получен {type(value)}")
    return value

def __readonly_check__(name, value, expected_type):
    value = __type_check__(name, value, expected_type)
    readonly_registry.add(name)
    return value

readonly_registry = set()

class ReadonlyDict(dict):
    def __setitem__(self, key, value):
        if key in readonly_registry and key in self:
            raise TypeError(f"Нельзя изменить значение readonly-переменной '{key}'")
        super().__setitem__(key, value)

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

def implements(*interfaces):
    def decorator(cls):
        for interface in interfaces:
            for attr in dir(interface):
                if not attr.startswith("__"):
                    if not hasattr(cls, attr):
                        raise TypeError(f"Класс {cls.__name__} не реализует требуемый атрибут '{attr}' интерфейса {interface.__name__}")
        return cls
    return decorator

def preprocess_source(source):
    if "use strict" in source:
        source = "__strict_mode__ = True\n" + source

    source = re.sub(r'(def\s+\w+)<[^>]+>\s*\(', lambda m: m.group(1) + "(", source)
    source = re.sub(r'^\s*type\s+(\w+)\s*=\s*(.+)$', r'\1 = \2', source, flags=re.MULTILINE)
    source = re.sub(r'(\w+)\?\s*:\s*([^\s=]+)', r'\1: Optional[\2]', source)
    source = re.sub(
        r'^\s*readonly\s+(\w+)\s*:\s*([^=]+)=\s*(.+)$',
        lambda m: f"{m.group(1)}: {m.group(2)}= __readonly_check__(\"{m.group(1)}\", {m.group(3)}, {m.group(2).strip()})",
        source, flags=re.MULTILINE
    )

    source = re.sub(r'^(\s*)private\s+(\w+)', lambda m: f"{m.group(1)}__{m.group(2)}", source, flags=re.MULTILINE)
    source = re.sub(r'^(\s*)protected\s+(\w+)', lambda m: f"{m.group(1)}_{m.group(2)}", source, flags=re.MULTILINE)
    source = re.sub(r'^(\s*)public\s+(\w+)', lambda m: f"{m.group(1)}{m.group(2)}", source, flags=re.MULTILINE)

    def interface_repl(match):
        name = match.group(1)
        return f"class {name}:\n    __is_interface__ = True"
    source = re.sub(r'^interface\s+(\w+)\s*:', interface_repl, source, flags=re.MULTILINE)

    def implements_repl(match):
        indent = match.group(1)
        class_name = match.group(2)
        interfaces = match.group(3)
        interfaces_list = [iface.strip() for iface in interfaces.split(',')]
        decorators = "".join([f"{indent}@implements({iface})\n" for iface in interfaces_list])
        return f"{decorators}{indent}class {class_name}:"
    source = re.sub(r'^(\s*)class\s+(\w+)\s+implements\s+([\w\s,]+)\s*:', implements_repl, source, flags=re.MULTILINE)

    def enum_repl(match):
        enum_name = match.group(1)
        body = match.group(2)
        lines = body.splitlines()
        enum_lines = []
        value = 1
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.endswith(','):
                line = line[:-1]
            enum_lines.append(f"    {line} = {value}")
            value += 1
        enum_body = "\n".join(enum_lines)
        return f"from enum import Enum\nclass {enum_name}(Enum):\n{enum_body}"
    source = re.sub(r'enum\s+(\w+)\s*:\s*(.*?)\n(?=\S)', enum_repl, source, flags=re.DOTALL)

    source = re.sub(r'(\S+)\s+as\s+(\w+)', r'__assert_type__(\1, \2)', source)
    
    return source

class TypeScriptTransformer(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        has_annotation = (node.returns is not None) or any(arg.annotation is not None for arg in node.args.args)
        if has_annotation:
            decorator = ast.Name(id='type_checked', ctx=ast.Load())
            node.decorator_list.insert(0, decorator)
        self.generic_visit(node)
        return node

    def visit_AnnAssign(self, node):
        if node.value is not None and isinstance(node.target, ast.Name):
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
        print("Использование: tpy_interpreter.py <файл.tpy>")
        sys.exit(1)
    file_path = sys.argv[1]
    if not file_path.endswith('.tpy'):
        print("Ошибка: файл должен иметь расширение .tpy")
        sys.exit(1)
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()
    processed_source = preprocess_source(source)
    tree = ast.parse(processed_source, filename=file_path)
    transformer = TypeScriptTransformer()
    tree = transformer.visit(tree)
    ast.fix_missing_locations(tree)
    code = compile(tree, filename=file_path, mode='exec')
    env = ReadonlyDict({
        'type_checked': type_checked,
        '__type_check__': __type_check__,
        '__assert_type__': __assert_type__,
        '__readonly_check__': __readonly_check__,
        'implements': implements,
        'inspect': inspect,
        '__name__': '__main__',
        'Optional': Optional,
    })
    exec(code, env)

if __name__ == '__main__':
    main()
