import unittest

from miner_py_src.call_graph import CFG


cfg_mock = {
    "teste.raise_exception": {
        "calls": [],
        "called_by": ["teste.except_caller"]
    },
    "teste.except_caller": {
        "calls": ["teste.raise_exception"],
        "called_by": ["teste.except_caught"]
    }
}


class TestCFG(unittest.TestCase):
    def test_flow_exception_handled(self):
        graph = CFG(cfg_mock,
                    {'teste.except_caller': ["ValueError"]})

        actual = graph.get_uncaught_exceptions('teste.raise_exception',
                                               ['ValueError'])
        expected = {}

        self.assertEqual(actual, expected)

    def test_flow_exception_unhandled(self):
        graph = CFG(cfg_mock,
                    {'teste.except_caller': ["ValueError"]})

        actual = graph.get_uncaught_exceptions('teste.raise_exception',
                                               ['ValueError', 'NewException'])

        expected = {'teste.except_caller': ['NewException']}

        self.assertEqual(actual, expected)

    def test_no_exception_handlers(self):
        graph = CFG(cfg_mock,{})

        actual = graph.get_uncaught_exceptions('teste.raise_exception',
                                               ['ValueError', 'NewException'])

        expected = {'teste.except_caller': ['ValueError', 'NewException']}

        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
