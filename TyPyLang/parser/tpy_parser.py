import ast
from preprocessor import preprocess_source
from transformer import TyPyTransformer

def parse_source(source: str, filename: str = "<string>") -> ast.Module:
    """Получение обработанного кода, потдерждиваемого .py компиляторами"""
    processed_source = preprocess_source(source)
    try:
        """перевод кода в дерево AST"""
        tree = ast.parse(processed_source, filename=filename)
    except SyntaxError as e:
        """
        получить обработанный код по строкам
        """
        lines = processed_source.splitlines()
        err_line = e.lineno or 0
        """
        (2 строки до и 2 строки после) вернуть ошибку
        """
        start = max(0, err_line - 3)
        end = min(len(lines), err_line + 2)
        context = "\n".join(f"{i+1:4}: {lines[i]}" for i in range(start, end))
        """
        Поднимаем новую ошибку с дополнительной информацией
        """
        raise SyntaxError(
            f"Ошибка компиляции в обработанном коде (файл {filename}, строка {err_line}):\n{context}"
        ) from e
    check_return_statements(tree)
    transformer = TyPyTransformer()
    tree = transformer.visit(tree)
    ast.fix_missing_locations(tree)
    return tree


def check_return_statements(tree: ast.AST):
    """
    Проходит по всем FunctionDef и, если у фукции есть анотация return любого типа джыннх (проверить кастомные типы),
    проверяет, что внутри есть хотя бы один return с выражением НУЖНОГО типа данных.
    Иначе — бросает SyntaxError (Создать свой EXCEPTION тип).
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.returns is not None:
            has_good_return = False
            for sub in ast.walk(node):
                if isinstance(sub, ast.Return) and sub.value is not None:
                    has_good_return = True
                    break
            if not has_good_return:
                raise SyntaxError(
                    f"Функция '{node.name}' объявлена как возвращающая "
                    f"{ast.unparse(node.returns)}, но в её теле нет ни одного "
                    f"return с возвращаемым значением "
                    f"(строка {node.lineno})."
                )