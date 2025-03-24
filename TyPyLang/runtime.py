import inspect
from enum import Enum
from typing import Optional

# Регистрация readonly-переменных
readonly_registry = set()

class ReadonlyDict(dict):
    def __setitem__(self, key, value):
        if key in readonly_registry and key in self:
            raise TypeError(f"Нельзя изменить значение readonly-переменной '{key}'")
        super().__setitem__(key, value)

def __assert_type__(value, expected_type):
    if not isinstance(value, expected_type):
        raise TypeError(f"Приведение типов: значение {value} не является {expected_type}")
    return value

def __type_check__(name, value, expected_type):
    if not isinstance(value, expected_type):
        raise TypeError(f"Переменная '{name}' должна быть {expected_type}, получен {type(value)}")
    return value

def __readonly_check__(name, value, expected_type):
    value = __type_check__(name, value, expected_type)
    readonly_registry.add(name)
    return value

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

"""
Собираем требования интерфейса (атрибуты и методы) с учётом наследования
"""
def gather_interface_requirements(interface):
    req_attrs = {}
    req_methods = {}
    for base in interface.__mro__:
        if getattr(base, '__is_interface__', False):
            req_attrs.update(getattr(base, '__annotations__', {}))
            for name, member in inspect.getmembers(base, predicate=inspect.isfunction):
                req_methods[name] = member
    return req_attrs, req_methods

def implements(*interfaces):
    def decorator(cls):
        orig_init = getattr(cls, '__init__', None)
        if not orig_init:
            raise TypeError(f"Класс {cls.__name__} должен иметь метод __init__ для проверки интерфейсов.")

        def new_init(self, *args, **kwargs):
            orig_init(self, *args, **kwargs)
            for interface in interfaces:
                req_attrs, req_methods = gather_interface_requirements(interface)
                for attr in req_attrs:
                    if not hasattr(self, attr):
                        raise TypeError(
                            f"Объект класса {cls.__name__} не реализует требуемый атрибут '{attr}' интерфейса {interface.__name__}"
                        )
                for name in req_methods:
                    if not (hasattr(self, name) and callable(getattr(self, name))):
                        raise TypeError(
                            f"Объект класса {cls.__name__} не реализует требуемый метод '{name}' интерфейса {interface.__name__}"
                        )
        cls.__init__ = new_init
        return cls
    return decorator
