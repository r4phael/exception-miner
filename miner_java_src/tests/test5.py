def multiple_try(x, y):
    a = x
    b = y
    try:
        # Floor Division : Gives only Fractional
        # Part as Answer
        result = a // b
        print("Yeah ! Your answer is :", result)
    except ZeroDivisionError:
        print("Sorry ! You are dividing by zero ")
    try:
        print("ok")
    except:
        pass


def run_(self, edit_token, cmd_args):
    cmd_args = self.filter_args(cmd_args)
    token = cmd_args['token']
    with lock:
        try:
            (fn, args, kwargs) = COMMANDS.pop(token)
        except KeyError:
            return
    edit = self.view.begin_edit(edit_token, self.name(), cmd_args)
    try:
        if wants_edit_object(fn):
            return self.run(token, fn, args[0], edit, *args[1:], **kwargs)
        else:
            return self.run(token, fn, *args, **kwargs)
    finally:
        self.view.end_edit(edit)
