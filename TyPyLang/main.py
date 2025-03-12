import sys
from typing import Optional
import inspect


from parser.tpy_parser import parse_source
from runtime import (
    type_checked, __type_check__, __assert_type__, __readonly_check__,
    implements, ReadonlyDict
)

def main():
    if len(sys.argv) < 2:
        print("Использование: python main.py <файл.tpy>") #must be a throw
        sys.exit(1)
    file_path = sys.argv[1]
    if not file_path.endswith('.tpy'):
        print("Ошибка: файл должен иметь расширение .tpy") #must be a throw
        sys.exit(1)
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()
    
    # AST для переработки сахара из кода
    tree = parse_source(source, filename=file_path)
    code = compile(tree, filename=file_path, mode='exec')
    
    # Окружение для ратайм
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
