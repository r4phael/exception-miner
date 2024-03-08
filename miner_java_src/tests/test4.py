def teste_string_linebreak(self):
    if self.module_name == "" and os.path.isdir(self.module_input):
        raise ValueError(
            "App not found.\n"
            "   Please use --simple if you are passing a "
            "directory to sanic.\n"
            f"   eg. sanic {self.module_input} --simple"
        )

    module = import_module(self.module_name)
    app = getattr(module, self.app_name, None)
    if self.as_factory:
        try:
            app = app(self.args)
        except TypeError:
            app = app()

def func():
    return True