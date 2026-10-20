"""Check that assembly preserves provenance instead of repairing model logic."""

import ast

import pytest

from workflow import assemble_patch, executable_body, extract_code, original_source, signature, target_name


def function(source, name):
    return next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name==name)


def test_preserve_original_docstring_and_generated_statements():
    response = '```python\n'+signature('BUG000')+'\n    return False\n```'
    result = assemble_patch('BUG000',response)
    final = function(result,target_name('BUG000'))
    original = function(original_source('BUG000'),target_name('BUG000'))
    generated = function(extract_code(response),target_name('BUG000'))
    assert ast.get_docstring(final)==ast.get_docstring(original)
    assert executable_body(final)==executable_body(generated)


def test_body_only_wrapping_keeps_relative_nesting():
    response='```python\nif node is None:\n    return None\nreturn node\n```'
    result=assemble_patch('BUG007',response)
    emitted=extract_code(response,target_name('BUG007'),signature('BUG007'))
    assert executable_body(function(result,target_name('BUG007')))==executable_body(function(emitted,target_name('BUG007')))


def test_misindented_fallback_is_rejected_not_fixed():
    response='```python\ndef reverse_linked_list(node):\n    while node:\n        return node\nreturn None\n```'
    with pytest.raises(ValueError,match='top-level'):
        assemble_patch('BUG007',response)


def test_changed_signature_is_rejected():
    response='```python\ndef reverse_linked_list(head):\n    return head\n```'
    with pytest.raises(ValueError,match='signature'):
        assemble_patch('BUG007',response)


def test_original_helpers_and_module_documentation_remain():
    original=original_source('BUG001')
    result=assemble_patch('BUG001','```python\n'+signature('BUG001')+'\n    return 0\n```')
    for name in ('get','insert_or_update'):
        assert ast.get_source_segment(original,function(original,name))==ast.get_source_segment(result,function(result,name))
    assert original[original.index('"""'):]==result[result.index('"""'):]


def test_example_function_is_not_reinterpreted_as_target():
    with pytest.raises(ValueError):
        assemble_patch('BUG007','```python\ndef total(items):\n    return sum(items)\n```')
