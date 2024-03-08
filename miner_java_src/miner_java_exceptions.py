class MinerJavaError(Exception):
    pass


class TryNotFoundException(MinerJavaError):
    pass


class ExceptClauseExpectedException(MinerJavaError):
    pass


class FunctionDefNotFoundException(MinerJavaError):
    pass


class TreeSitterNodeException(MinerJavaError):
    pass


class CallGraphError(MinerJavaError):
    pass

