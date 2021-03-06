"""Tests for matcher.py."""


from pytype import abstract
from pytype import matcher
from pytype.pytd import cfg

import unittest


class FakeVM(object):

  def __init__(self):
    self.program = cfg.Program()


class MatcherTest(unittest.TestCase):
  """Test matcher.AbstractMatcher."""

  def setUp(self):
    self.matcher = matcher.AbstractMatcher()
    self.vm = FakeVM()
    self.root_cfg_node = self.vm.program.NewCFGNode("root")

  def _match_var(self, left, right):
    var = self.vm.program.NewVariable("foo")
    left_binding = var.AddBinding(left)
    return self.matcher.match_var_against_type(
        var, right, {}, self.root_cfg_node, {var: left_binding})

  def _match_value(self, left, right):
    var = self.vm.program.NewVariable("foo")
    left_binding = var.AddBinding(left)
    return self.matcher.match_value_against_type(
        left_binding, right, {}, self.root_cfg_node, {var: left_binding})

  def testBasic(self):
    result = self._match_var(abstract.Empty(self.vm), abstract.Nothing(self.vm))
    self.assertEquals(result, {})

  def testType(self):
    left = abstract.InterpreterClass("dummy", [], {}, None, self.vm)
    right = abstract.InterpreterClass("type", [], {}, None, self.vm)
    type_parameters = {abstract.T: abstract.TypeParameter(abstract.T, self.vm)}
    other_type = abstract.ParameterizedClass(right, type_parameters, self.vm)
    other_type.module = "__builtin__"
    result = self._match_value(left, other_type)
    instance_binding, = result[abstract.T].bindings
    cls_binding, = instance_binding.data.cls.bindings
    self.assertEquals(cls_binding.data, left)

  def testUnion(self):
    left_option1 = abstract.InterpreterClass("o1", [], {}, None, self.vm)
    left_option2 = abstract.InterpreterClass("o2", [], {}, None, self.vm)
    left = abstract.Union([left_option1, left_option2], self.vm)
    other_type = abstract.InterpreterClass("type", [], {}, None, self.vm)
    other_type.module = "__builtin__"
    result = self._match_value(left, other_type)
    self.assertEquals(result, {})

  def testMetaclass(self):
    left = abstract.InterpreterClass("left", [], {}, None, self.vm)
    meta1 = abstract.InterpreterClass("m1", [], {}, None, self.vm)
    meta2 = abstract.InterpreterClass("m2", [], {}, None, self.vm)
    left.cls = self.vm.program.NewVariable(
        "cls", [meta1, meta2], [], self.root_cfg_node)
    result1 = self._match_value(left, meta1)
    result2 = self._match_value(left, meta2)
    self.assertEquals(result1, {})
    self.assertEquals(result2, {})

  def testEmptyAgainstClass(self):
    var = self.vm.program.NewVariable("foo")
    right = abstract.InterpreterClass("bar", [], {}, None, self.vm)
    result = self.matcher.match_var_against_type(
        var, right, {}, self.root_cfg_node, {})
    self.assertEquals(result, {})

  def testEmptyAgainstNothing(self):
    var = self.vm.program.NewVariable("foo")
    right = abstract.Nothing(self.vm)
    result = self.matcher.match_var_against_type(
        var, right, {}, self.root_cfg_node, {})
    self.assertEquals(result, {})

  def testEmptyAgainstTypeParameter(self):
    var = self.vm.program.NewVariable("foo")
    right = abstract.TypeParameter("T", self.vm)
    result = self.matcher.match_var_against_type(
        var, right, {}, self.root_cfg_node, {})
    self.assertItemsEqual(result, ["T"])
    self.assertFalse(result["T"].bindings)

  def testEmptyAgainstUnsolvable(self):
    var = self.vm.program.NewVariable("foo")
    right = abstract.Empty(self.vm)
    result = self.matcher.match_var_against_type(
        var, right, {}, self.root_cfg_node, {})
    self.assertEquals(result, {})


if __name__ == "__main__":
  unittest.main()
