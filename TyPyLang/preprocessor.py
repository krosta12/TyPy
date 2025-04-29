import re

def preprocess_source(source):
    """Teisendab TyPy laiendatud süntaksi tavalise Python-koodiks."""

    """Обрабатываем код с директивой 'use strict'"""
    strict_present = bool(re.search(r'^(?!\s*#)\s*use strict\s*$', source, flags=re.MULTILINE))
    
    """
    Если "use strict" найден, добавляем переменную __strict_mode__
    """
    source = re.sub(r'^(?!\s*#)\s*use strict\s*$', '', source, flags=re.MULTILINE)
    
    if strict_present:
        source = "__strict_mode__ = True\n" + source

    """
    Удаляем директиву "use strict" из исходного кода
    """
    source = re.sub(r'^(?!\s*#)\s*use strict\s*$', '', source, flags=re.MULTILINE)

    """
    Проверяем правильность структуры каждлого кстомного елемента
    """
    if re.search(r"interface\s+\w+\s+def", source):
        raise SyntaxError("Invalid interface declaration syntax")

    if re.search(r"enum\s+\w+\s+\w+", source):
        raise SyntaxError("Invalid enum declaration syntax")
    """
    Удаляем параметры обобщений в определениях функций
    """
    source = re.sub(r'^(?!\s*#)(def\s+\w+)<[^>]+>\s*\(', lambda m: m.group(1) + "(", source, flags=re.MULTILINE)
    source = re.sub(r'<[^>]+>', '', source)
    source = re.sub(r':\s*[A-Z]\b', ': object', source)

    """
    Обработка type alias: преобразуем "type Alias = SomeType
    """
    source = re.sub(r'^(?!\s*#)\s*type\s+(\w+)\s*=\s*(.+)$', r'\1 = \2', source, flags=re.MULTILINE)

    """
    Обработка optional: "variable?: Type" => "variable: Optional[Type] = None"
    """
    source = re.sub(
        r'^(?!\s*#)(\s*)(\w+)\?\s*:\s*([^\s=]+)',
        r'\1\2: Optional[\3] = None',
        source,
        flags=re.MULTILINE
    )

    """
    Обработка readonly-переменных: "readonly x: int = expr" => "x: int = __readonly_check__(...)"
    """
    source = re.sub(
        r'^(?!\s*#)\s*readonly\s+(\w+)\s*:\s*([^=]+)=\s*(.+)$',
        lambda m: f"{m.group(1)}: {m.group(2)} = __readonly_check__(\"{m.group(1)}\", {m.group(3)}, {m.group(2).strip()})",
        source, flags=re.MULTILINE
    )

    """    
    Обработка модификаторов доступа (private, protected, public)
    """
    source = re.sub(r'^(?!\s*#)(\s*)private\s+(\w+)', lambda m: f"{m.group(1)}__{m.group(2)}", source, flags=re.MULTILINE)
    source = re.sub(r'^(?!\s*#)(\s*)protected\s+(\w+)', lambda m: f"{m.group(1)}_{m.group(2)}", source, flags=re.MULTILINE)
    source = re.sub(r'^(?!\s*#)(\s*)public\s+(\w+)', lambda m: f"{m.group(1)}{m.group(2)}", source, flags=re.MULTILINE)

    """
    Обработка интерфейсов: заменяем "interface Name:" на определение класса с меткой __is_interface__
    """
    def interface_repl(match):
        name = match.group(1)
        extends_part = match.group(2)
        if extends_part:
            bases = ','.join(base.strip() for base in extends_part.split(','))
            return f"class {name}({bases}):\n    __is_interface__ = True\n"
        else:
            return f"class {name}:\n    __is_interface__ = True\n"
    source = re.sub(r'^\s*interface\s+(\w+)(?:\s+extends\s+([\w\s,]+))?:\s*', interface_repl, source, flags=re.MULTILINE)

    source = re.sub(
        r'^(\s*)(?!@access_controlled)(class\s+\w+(?!.*__is_interface__)(?:\([^)]*\))?:)',
        lambda m: f"{m.group(1)}@access_controlled\n{m.group(1)}{m.group(2)}",
        source, flags=re.MULTILINE
    )
    
    """
    Обработка enum: "enum Name: ... " -> "class Name(Enum): ..."
    """
    def enum_repl(match):
        enum_name = match.group(1)
        body = match.group(2)
        
        # разбиваем тело на строки
        lines = [line.strip() for line in body.splitlines() if line.strip()]
        enum_lines = []
        value = 0  # индексируем Енум
        
        for line in lines:
            # проверяем, содержит ли строка запятые для линейного объявления
            if ',' in line:
                # сплитим элементы через запятые
                elements = [elem.strip() for elem in line.split(',') if elem.strip()]
                for elem in elements:
                    if '=' in elem:
                        # обрабатываем явное значение
                        name_part, val_part = elem.split('=', 1)
                        name_part = name_part.strip()
                        val_part = val_part.strip()
                        enum_lines.append(f"    {name_part} = {val_part}")
                        # обновляем значение для следующих элементов
                        try:
                            value = int(val_part) + 1
                        except ValueError:
                            # если значение не целое число, продолжим с текущего value
                            value += 1
                    else:
                        # аавтозначение
                        enum_lines.append(f"    {elem} = {value}")
                        value += 1
            else:
                if '=' in line:
                    name_part, val_part = line.split('=', 1)
                    name_part = name_part.strip()
                    val_part = val_part.strip()
                    enum_lines.append(f"    {name_part} = {val_part}")
                    try:
                        value = int(val_part) + 1
                    except ValueError:
                        value += 1
                else:
                    enum_lines.append(f"    {line} = {value}")
                    value += 1
        
        enum_body = "\n".join(enum_lines)

        enum_body += "\n    def __str__(self):\n        return str(self.value)"
        enum_body += "\n    __repr__ = __str__"
        return f"from enum import Enum\nclass {enum_name}(Enum):\n{enum_body}\n"

    source = re.sub(r'^\s*enum\s+(\w+):\s*\n((?:\s+.+\n*)+)', enum_repl, source, flags=re.MULTILINE)

    """
    Обработка implements: добавляем декораторы @implements(...)
    """
    def implements_repl(match):
        indent = match.group(1)
        class_name = match.group(2)
        inheritance = match.group(3) if match.group(3) else ""
        interfaces = match.group(4)
        interfaces_list = [iface.strip() for iface in interfaces.split(',')]
        decorators = "".join([f"{indent}@implements({iface})\n" for iface in interfaces_list])
        return f"{decorators}{indent}class {class_name}{inheritance}:"
    
    source = re.sub(
        r'^(?!\s*#)(\s*)class\s+(\w+)(\s*\([^)]*\))?\s+implements\s+([\w\s,]+)\s*:',
        implements_repl,
        source, flags=re.MULTILINE
    )

    """
    Обработка приведения типов (assertion): "expr as Type" -> "__assert_type__(expr, Type)"
    """
    source = re.sub(r'(?<!#)(\S+)\s+as\s+(\w+)\b(?!:)', r'__assert_type__(\1, \2)', source)

    """
    Проверка корректности определения методов в интерфейсах
    """
    source = check_interface_methods(source)
    
    # фиксим табуляцию
    source = fix_interface_body(source)
    
    return source

def check_interface_methods(source):
    #проверка наличия тела методав  в интерфейсе
    lines = source.splitlines()
    for i, line in enumerate(lines):
        # Ищем объявления классов, mis on liidesed (märkmed __is_interface__)
        m = re.match(r'^(?!\s*#)\s*class\s+(\w+)(?:\s*\([^)]*\))?:\s*$', line)
        if m:
            interface_name = m.group(1)
            # Если в следующих строках до конца блока найдём метод без тела – ошибка.
            j = i + 1
            while j < len(lines):
                current_line = lines[j]
                if not current_line.startswith("    "):
                    break
                # Если строка определяет метод
                method_match = re.match(r'^\s*def\s+(\w+)\(.*\):\s*$', current_line)
                if method_match:
                    method_indent = len(re.match(r'^(\s*)', current_line).group(1))
                    # Если следующая строка отсутствует или имеет отступ не больше, чем у заголовка метода, считаем, что тело метода отсутствует
                    if j + 1 >= len(lines) or (lines[j+1].strip() == '' or len(re.match(r'^(\s*)', lines[j+1]).group(1)) <= method_indent):
                        raise SyntaxError(f"Интерфейс {interface_name}: метод {method_match.group(1)} не имеет тела. Проверьте отступы (например, добавьте 'pass').")
                j += 1
    return "\n".join(lines)

def fix_interface_body(source):
    """
    Функция исправляет отступы блока интерфейса
    """
    lines = source.splitlines()
    new_lines = []
    in_interface = False
    for i, line in enumerate(lines):
        if re.match(r'^\s*class\s+\w+(?:\s*\([^)]*\))?:\s*$', line):
            new_lines.append(line)
            in_interface = False
        elif "__is_interface__" in line:
            new_lines.append(line)
            in_interface = True
        elif in_interface:
            if line.strip() != "":
                new_lines.append("    " + line.lstrip())
            else:
                new_lines.append(line)
            if i+1 < len(lines) and not lines[i+1].startswith("    "):
                in_interface = False
        else:
            new_lines.append(line)
    return "\n".join(new_lines)

def preprocess_generic_functions(source: str) -> str:
    """
    Обработка функций с дженериками: def identity<T>(v: T) -> T
    превращаем в нормальный Python код с TypeVar
    """
    pattern = r"def\s+(\w+)<([\w,\s]+)>\s*\("
    
    typevar_set = set()
    new_source_lines = []
    last_pos = 0

    for match in re.finditer(pattern, source):
        start, end = match.span()
        func_name = match.group(1)
        type_vars = match.group(2).replace(' ', '').split(',')

        typevar_set.update(type_vars)

        # деалем субстринг
        new_source_lines.append(source[last_pos:start])
        # правильный def без <T>
        new_source_lines.append(f"def {func_name}(")
        last_pos = end

    # остаток кода
    new_source_lines.append(source[last_pos:])

    new_source = ''.join(new_source_lines)

    # если найдены дженерики — вставляем в начало импорты
    if typevar_set:
        insert_block = "from typing import TypeVar\n" + "".join(
            f"{name} = TypeVar('{name}')\n" for name in sorted(typevar_set)
        ) + "\n\n"
        new_source = insert_block + new_source

    return new_source
