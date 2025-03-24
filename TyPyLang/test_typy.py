import unittest
import re
from preprocessor import preprocess_source, check_interface_methods
from runtime import (
    __assert_type__, __type_check__, __readonly_check__,
    type_checked, gather_interface_requirements, implements, ReadonlyDict
)
import inspect

# Тестирование транслятора
class TestPreprocessor(unittest.TestCase):

    def test_use_strict_removal(self):
        # Удалить useStrict
        source = """
        use strict
        print('Hello')
        """
        processed = preprocess_source(source)
        self.assertNotIn("use strict", processed)
        self.assertIn("__strict_mode__ = True", processed)

    def test_type_alias(self):
        source = """
        type MyInt = int
        x = 5
        """
        processed = preprocess_source(source)
        self.assertIn("MyInt = int", processed)
        self.assertNotIn("type MyInt =", processed)

    def test_optional_conversion(self):
        source = """value?: str = 'hello'"""
        processed = preprocess_source(source)
        # Должно заменить на: value: Optional[str]
        self.assertIn("value: Optional[str]", processed)

    def test_interface_rewriting_no_extends(self):
        source = """
        interface MyInterface:
            def method(self): pass
        """
        processed = preprocess_source(source)
        # Должно преобразоваться в класс с флагом __is_interface__
        self.assertIn("class MyInterface:", processed)
        self.assertIn("__is_interface__ = True", processed)

    def test_interface_rewriting_with_extends(self):
        source = """
        interface Child extends Parent, Other:
            def child_method(self): pass
        """
        processed = preprocess_source(source)
        # Проверяем, что базовые интерфейсы перечислены
        self.assertIn("class Child(Parent,Other):", processed)
        self.assertIn("__is_interface__ = True", processed)

    def test_enum_rewriting(self):
        source = """
        enum Color:
            Red,
            Green,
            Blue
            
            print(Color.Red)
        """
        processed = preprocess_source(source)
        self.assertIn("class Color(Enum):", processed)
        self.assertIn("Red = 1", processed)
        self.assertIn("Blue = 3", processed)

    def test_assertion_rewriting(self):
        source = "a = 123 as int"
        processed = preprocess_source(source)
        self.assertNotIn("as int", processed)
        self.assertIn("__assert_type__(123, int)", processed)

    def test_ignores_commented_lines(self):
        source = """
        # use strict
        # type Alias = int
        # """
        processed = preprocess_source(source)
        self.assertIn("# use strict", processed)
        self.assertIn("# type Alias = int", processed)

    def test_implements_rewriting(self):
        source = """
        class MyClass implements InterfaceA, InterfaceB:
            pass
        """
        processed = preprocess_source(source)
        self.assertIn("@implements(InterfaceA)", processed)
        self.assertIn("@implements(InterfaceB)", processed)
        self.assertIn("class MyClass:", processed)

    def test_check_interface_methods_error(self):
        # Проверяем, что если метод интерфейса не имеет тела, возникает ошибка
        source = """
        interface Bad:
            def missing(self):
        """
        with self.assertRaises(SyntaxError):
            _ = check_interface_methods(source)


# Тесты кода
class TestRuntimeFunctions(unittest.TestCase):

    def test_assert_type_correct(self):
        self.assertEqual(__assert_type__(123, int), 123)
        self.assertEqual(__assert_type__("abc", str), "abc")
    
    def test_assert_type_incorrect(self):
        with self.assertRaises(TypeError):
            __assert_type__(123, str)
        with self.assertRaises(TypeError):
            __assert_type__(None, int)
    
    def test_type_check_correct(self):
        self.assertEqual(__type_check__("x", 5, int), 5)
    
    def test_type_check_incorrect(self):
        with self.assertRaises(TypeError):
            __type_check__("x", "not an int", int)
    
    def test_readonly_check(self):
        # Первый вызов должен сработать
        value = __readonly_check__("const_var", 10, int)
        self.assertEqual(value, 10)
        # Второй вызов для той же переменной должен вызывать ошибку
        # Эмулируем окружение через ReadonlyDict
        env = ReadonlyDict({"const_var": value})
        with self.assertRaises(TypeError):
            env["const_var"] = 20

    def test_type_checked_decorator_correct(self):
        @type_checked
        def add(a: int, b: int) -> int:
            return a + b
        self.assertEqual(add(2, 3), 5)
    
    def test_type_checked_decorator_incorrect_arg(self):
        @type_checked
        def add(a: int, b: int) -> int:
            return a + b
        with self.assertRaises(TypeError):
            add("a", "b")
    
    def test_type_checked_decorator_incorrect_return(self):
        @type_checked
        def to_str(a: int) -> int:
            return str(a)
        with self.assertRaises(TypeError):
            to_str(5)
    
    def test_gather_interface_requirements_simple(self):
        # Определим интерфейс вручную как класс
        class ITest:
            __is_interface__ = True
            a: int
            def foo(self): pass
        req_attrs, req_methods = gather_interface_requirements(ITest)
        self.assertIn("a", req_attrs)
        self.assertIn("foo", req_methods)
    
    def test_gather_interface_requirements_inheritance(self):
        # Интерфейс с наследованием
        class IBase:
            __is_interface__ = True
            b: int
            def base_method(self): pass
        class IDerived(IBase):
            __is_interface__ = True
            c: int
            def derived_method(self): pass
        req_attrs, req_methods = gather_interface_requirements(IDerived)
        self.assertIn("b", req_attrs)
        self.assertIn("c", req_attrs)
        self.assertIn("base_method", req_methods)
        self.assertIn("derived_method", req_methods)
    
    def test_implements_decorator_success(self):
        # Определяем интерфейс
        class IExample:
            __is_interface__ = True
            x: int
            def foo(self): pass
        @implements(IExample)
        class Good:
            x: int
            def __init__(self, x):
                self.x = x
            def foo(self):
                return self.x
        # Создание объекта не должно выдавать ошибку
        obj = Good(10)
        self.assertEqual(obj.foo(), 10)
    
    def test_implements_decorator_missing_attr(self):
        class IExample:
            __is_interface__ = True
            x: int
            def foo(self): pass
        @implements(IExample)
        class MissingAttr:
            def __init__(self, x):
                # Не задаём атрибут x
                pass
            def foo(self):
                return 0
        with self.assertRaises(TypeError):
            _ = MissingAttr(5)
    
    def test_implements_decorator_missing_method(self):
        class IExample:
            __is_interface__ = True
            x: int
            def foo(self): pass
        @implements(IExample)
        class MissingMethod:
            x: int
            def __init__(self, x):
                self.x = x
            # Отсутствует метод foo
        with self.assertRaises(TypeError):
            _ = MissingMethod(5)
    
    def test_implements_decorator_inheritance_interface(self):
        class IA:
            __is_interface__ = True
            a: int
            def foo(self): pass
        class IB(IA):
            __is_interface__ = True
            b: int
            def bar(self): pass
        @implements(IB)
        class Complete:
            a: int
            b: int
            def __init__(self, a, b):
                self.a = a
                self.b = b
            def foo(self):
                return self.a
            def bar(self):
                return self.b
        obj = Complete(1, 2)
        self.assertEqual(obj.foo(), 1)
        self.assertEqual(obj.bar(), 2)

if __name__ == '__main__':
    unittest.main()
