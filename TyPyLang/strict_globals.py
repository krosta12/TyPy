class StrictGlobals(dict):
    def __init__(self, *args, readonly_registry=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.readonly_registry = readonly_registry or set()

    def __setitem__(self, key, value):
        if key in self.readonly_registry:
            raise TypeError(f"Переменная '{key}' объявлена как readonly и не может быть переопределена.")
        super().__setitem__(key, value)
