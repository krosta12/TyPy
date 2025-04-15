class StrictGlobals(dict):
    def __setitem__(self, key, value):
        if key in self:
            raise TypeError(f"Переменная '{key}' уже определена и нельзя переопределить в строгом режиме.")
        super().__setitem__(key, value)
