import inspect
from enum import Enum
from typing import Optional  #have to realise

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

def implements(*interfaces):
    def decorator(cls):
        for interface in interfaces:
            for attr in dir(interface):
                if not attr.startswith("__"):
                    if not hasattr(cls, attr):
                        raise TypeError(f"Класс {cls.__name__} не реализует требуемый атрибут '{attr}' интерфейса {interface.__name__}")
        return cls
    return decorator
