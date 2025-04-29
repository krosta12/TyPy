def Access_controlled(cls):
    """
    - private атрибуты начинаются с двух подчеркиваний (__attr)
    - protected атрибуты начинаются с одного подчеркивания (_attr)
    - public атрибуты не имеют подчеркиваний
    """
    original_init = cls.__init__
    
    def new_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        original_setattr = self.__class__.__setattr__
    
        def secured_setattr(obj, name, value):
            if name in obj.__dict__:
                if name.startswith("__") and not name.endswith("__"):
                    raise AttributeError(f"Нарушение прав доступа: нельзя переопределить private атрибут '{name}'")
                if name.startswith("_") and not name.startswith("__"):
                    raise AttributeError(f"Нарушение прав доступа: нельзя переопределить protected атрибут '{name}'")
            original_setattr(obj, name, value)
        self.__class__.__setattr__ = secured_setattr
        cls.__init__ = new_init
    return cls