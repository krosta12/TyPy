class StrictGlobals(dict):
    def __init__(self, *args, readonly_registry=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.readonly_registry = readonly_registry or set()

    def __setitem__(self, key, value):
        if key in self.readonly_registry:
            raise TypeError(f"Variable '{key}' declared as readonly and can't be rewrited.")
        super().__setitem__(key, value)
