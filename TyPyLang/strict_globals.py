class StrictGlobals(dict):
    def __init__(self, *args, readonly_registry=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.readonly_registry = readonly_registry or set()

    def __setitem__(self, key, value):
        if isinstance(value, BaseException):
            super().__setitem__(key, value)
            return
        if key in self:
            if key in self.readonly_registry:
                raise TypeError(f"Переменная '{key}' уже определена как readonly и нельзя переопределить.")
            super().__setitem__(key, value)  #если не readonly то пишесм
        else:
            super().__setitem__(key, value)



