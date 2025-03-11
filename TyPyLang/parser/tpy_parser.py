import ast

from preprocessor import preprocess_source
from transformer import TyPyTransformer

def parse_source(source: str, filename: str = "<string>") -> ast.Module:
    # Предобработка исходного кода для поддержки расширенного синтаксиса (удаление нового синтьаксиса)
    processed_source = preprocess_source(source)
    # Парсинг в AST
    tree = ast.parse(processed_source, filename=filename)
    # Применяем трансформации для проверки типов и других преобразований
    transformer = TyPyTransformer()
    tree = transformer.visit(tree)
    ast.fix_missing_locations(tree)
    return tree
