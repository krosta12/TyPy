import sys
from typing import Optional
import inspect
from strict_globals import StrictGlobals


from parser.tpy_parser import parse_source
from runtime import (
    type_checked, __type_check__, __assert_type__, __readonly_check__,
    implements, ReadonlyDict
)

"""Главный исполнитель преобразования и запуска кода"""

def main():

    if len(sys.argv) < 2:
        print("Использование: python main.py <файл.tpy>") #must be a throw
        sys.exit(1)

    file_path = sys.argv[1]

    if not file_path.endswith('.tpy'):
        print("Ошибка: файл должен иметь расширение .tpy") #must be a throw
        sys.exit(1)
    
    """Начать чтение из файла и записать всё в оперативную память"""
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()
    
    """Перерабьотка кода в AST для работы с синтаксисами"""
    tree = parse_source(source, filename=file_path)
    code = compile(tree, filename=file_path, mode='exec')
    
    """
    Создание окружения при помощи ReadonlyDict
    передача функций в окружение
    """
    env = StrictGlobals({
        'type_checked': type_checked,
        '__type_check__': __type_check__,
        '__assert_type__': __assert_type__,
        '__readonly_check__': __readonly_check__,
        'implements': implements,
        'inspect': inspect,
        '__name__': '__main__',
        'Optional': Optional,
})

    """запуск кастомного окружения"""
    exec(code, env)

if __name__ == '__main__':
    main()
