def Access_controlled(cls):
    original_setattr = cls.__setattr__

    def new_setattr(self, key, value):
        if key in self.__dict__:
            if key.startswith("__") and not key.endswith("__"):
                raise AttributeError(f"Нарушение прав доступа: нельзя переопределить private атрибут '{key}'")
            if key.startswith("_") and not key.startswith("__"):
                raise AttributeError(f"Нарушение прав доступа: нельзя переопределить protected атрибут '{key}'")
        original_setattr(self, key, value)

    cls.__setattr__ = new_setattr
    return cls
