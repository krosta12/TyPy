import inspect
from enum import Enum
from typing import Optional, Union, get_origin, get_args

from strict_globals import StrictGlobals
from access_controlled import Access_controlled

# readonly vars registration
readonly_registry = set()

class ReadonlyDict(dict):
    def __setitem__(self, key, value):
        if key in readonly_registry and key in self:
            raise TypeError(f"Cannot change the value of a readonly variable '{key}'")
        super().__setitem__(key, value)

def __assert_type__(value, expected_type):
    if not isinstance(value, expected_type):
        raise TypeError(f"Type assertion: the value {value} is not a {expected_type}")
    return value

def __type_check__(name, value, expected_type):
    if not isinstance(value, expected_type):
        raise TypeError(f"variable '{name}' must be a {expected_type}, got {type(value)}")
    return value

def __readonly_check__(name, value, expected_type):
    if name in readonly_registry:
        raise TypeError(f"Variable '{name}' declared as readonly.")
    readonly_registry.add(name)
    return __type_check__(name, value, expected_type)

def type_checked(func):
    def wrapper(*args, **kwargs):
        annotations = func.__annotations__
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        for name, value in bound_args.arguments.items():
            if name in annotations:
                expected = annotations[name]
                # argument type Checking
                if not isinstance(expected, type) and hasattr(expected, '__origin__'):
                    # Checking for Optional and Union types
                    origin = get_origin(expected)
                    args_type = get_args(expected)
                    if origin is Union:
                        if not any(isinstance(value, arg) for arg in args_type):
                            raise TypeError(f"Argument '{name}' must be {expected}, got a {type(value)}")
                    elif origin and not isinstance(value, origin):
                        raise TypeError(f"Argument '{name}' must be {expected}, got a {type(value)}")
                elif isinstance(expected, type) and not isinstance(value, expected):
                    raise TypeError(f"Argument '{name}' must be {expected}, got a {type(value)}")

        result = func(*args, **kwargs)
        if 'return' in annotations and annotations['return'] is not None:
            expected = annotations['return']
            # Checking the return value
            if not isinstance(expected, type) and hasattr(expected, '__origin__'):
                # Processing types like Optional, Union, etc.
                origin = get_origin(expected)
                args_type = get_args(expected)
                if origin is Union:
                    if not any(isinstance(result, arg) for arg in args_type):
                        raise TypeError(f"Function must return {expected}, got a {type(result)}")
                elif origin and not isinstance(result, origin):
                    raise TypeError(f"Function must return {expected}, got a {type(result)}")
            elif isinstance(expected, type) and not isinstance(result, expected):
                raise TypeError(f"Function must return {expected}, got a {type(result)}")

        return result
    return wrapper

"""
Kogume liidese nõuded (atribuudid ja meetodid), arvestades pärimist
"""
def gather_interface_requirements(interface):
    req_attrs = {}
    req_methods = {}
    for base in interface.__mro__:
        if getattr(base, '__is_interface__', False):
            req_attrs.update(getattr(base, '__annotations__', {}))
            for name, member in inspect.getmembers(base, predicate=inspect.isfunction):
                if name != '__init__':
                    req_methods[name] = member
    return req_attrs, req_methods

def implements(*interfaces):
    def decorator(cls):
        orig_init = cls.__init__ 
        def new_init(self, *args, **kwargs):
            orig_init(self, *args, **kwargs)
            for interface in interfaces:
                req_attrs, req_methods = gather_interface_requirements(interface)
                for attr in req_attrs:
                    if not hasattr(self, attr):
                        raise TypeError(
                            f"Class '{cls.__name__}' does not implement the required attribute '{attr}' from interface '{interface.__name__}'"
                        )
                for name in req_methods:
                    if not (hasattr(self, name) and callable(getattr(self, name))):
                        raise TypeError(
                            f"Class '{cls.__name__}' does not implement the required method '{name}' (from interface '{interface.__name__}')"
                        )
        cls.__init__ = new_init
        return cls
    return decorator


