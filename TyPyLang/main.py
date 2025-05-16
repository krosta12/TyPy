import sys
from typing import Optional, Union, get_origin, get_args
import inspect
from enum import Enum
from strict_globals import StrictGlobals


from parser.tpy_parser import parse_source
from preprocessor import preprocess_generic_functions, preprocess_source
from runtime import readonly_registry
from runtime import (
    type_checked, __type_check__, __assert_type__, __readonly_check__,
    implements, Access_controlled
)
"""Koodi teisendamise ja käivitamise peamine täitja"""

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <file.tpy>") #must be a throw
        sys.exit(1)

    file_path = sys.argv[1]

    if not file_path.endswith('.tpy'):
        print("Error: The file must have a .tpy extension") #must be a throw
        sys.exit(1)
    
    """Alusta failist lugemist ja kirjuta kõik operatiivmällu"""
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()

    """Koodi ümbertöötamine AST-ks (abstraktseks süntaksipuuks) süntaksitöötluseks"""
    source = preprocess_generic_functions(source)

    tree = parse_source(source, filename=file_path)
    code = compile(tree, filename=file_path, mode='exec')
    
    """
    Keskkonna loomine kasutades ReadonlyDict
    funktsioonide edastamine keskkonda
    """
    env = StrictGlobals({
        'type_checked': type_checked,
        '__type_check__': __type_check__,
        '__assert_type__': __assert_type__,
        '__readonly_check__': __readonly_check__,
        'implements': implements,
        'access_controlled': Access_controlled,
        'inspect': inspect,
        '__name__': '__main__',
        'Optional': Optional,
        'Union': Union,
        'get_origin': get_origin,
        'get_args': get_args,
        'Enum': Enum,
    }, readonly_registry=readonly_registry)

    exec(code, env)

if __name__ == '__main__':
    main()