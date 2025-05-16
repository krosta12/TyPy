def Access_controlled(cls):
    """
    - Privaatsed atribuudid algavad kahe allkriipsuga (__attr)
    - protected atribuudid algavad ühe allkriipsuga (_attr)
    - public atribuudid ei sisalda allkriipse (attr)
    """
    original_init = cls.__init__
    
    def new_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        original_setattr = self.__class__.__setattr__
    
        def secured_setattr(obj, name, value):
            if name in obj.__dict__:
                if name.startswith("__") and not name.endswith("__"):
                    raise AttributeError(f"Access violation: cannot override a private attribute '{name}'")
                if name.startswith("_") and not name.startswith("__"):
                    raise AttributeError(f"Access violation: cannot override a protected attribute '{name}'")
            original_setattr(obj, name, value)
        self.__class__.__setattr__ = secured_setattr
        cls.__init__ = new_init
    return cls