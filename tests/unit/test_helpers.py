import pytest

from local_operator.helpers import (
    clean_json_response,
    clean_plain_text_response,
    remove_think_tags,
)


@pytest.mark.parametrize(
    "response_content, expected_output",
    [
        ("This is a test <think>with think tags</think>.", "This is a test ."),
        ("No think tags here.", "No think tags here."),
        ("<think>Only think tags</think>", ""),
        ("<think>Think tags leading content</think> content", "content"),
        ("", ""),
    ],
)
def test_remove_think_tags(response_content, expected_output):
    """
    Test the remove_think_tags function with various inputs.

    Args:
        response_content (str): The input string containing <think> tags.
        expected_output (str): The expected output string after removing <think> tags.
    """
    assert remove_think_tags(response_content) == expected_output


@pytest.mark.parametrize(
    "response_content, expected_output",
    [
        ("", ""),
        ("Just plain text", "Just plain text"),
        ("Line 1\nLine 2", "Line 1\nLine 2"),
        ("Text with  multiple   spaces", "Text with multiple spaces"),
        ("Text with trailing spaces  \n  Line 2  ", "Text with trailing spaces\nLine 2"),
        (
            "Here's a reflection:\n```python\nprint('hello world')\n```\nThis is important.",
            "Here's a reflection:\n\nThis is important.",
        ),
        (
            "Here's a reflection:\n```python\nprint('hello world')\n",
            "Here's a reflection:",
        ),
        ("Normal text without code blocks.", "Normal text without code blocks."),
        ('```json\n{"key": "value"}\n```\nAfter the code block.', "After the code block."),
        ("Before\n```\nUnspecified code block\n```\nAfter", "Before\n\nAfter"),
        ("```python\nMultiple\nLines\nOf\nCode\n```", ""),
        (
            '{\n"action": "EXECUTE_CODE",\n"code": "print(\'test\')"\n}',
            "",
        ),
        ('main content {"json": "value" }', "main content"),
        ('main content {"json": "value" } following text', "main content following text"),
        ('{"simple_key": "value"}', ""),
        (
            'Multiline\n\nInput\n\nI will respond with a message explaining my action. {"response":"Example response","code":"","content":"","file_path":"","mentioned_files":[],"replacements":[],"action":"DONE","learnings":"Example learnings"}',  # noqa: E501
            "Multiline\n\nInput\n\nI will respond with a message explaining my action.",
        ),
    ],
)
def test_clean_plain_text_response(response_content, expected_output):
    """
    Test the clean_plain_text_response function with various inputs.

    Args:
        response_content (str): The input string containing code blocks or JSON.
        expected_output (str): The expected output string after cleaning.
    """
    assert clean_plain_text_response(response_content) == expected_output


@pytest.mark.parametrize(
    "response_content, expected_output",
    [
        pytest.param(
            '```json\n{"action": "EXECUTE_CODE", "code": "print(\'test\')"}\n```',
            '{"action": "EXECUTE_CODE", "code": "print(\'test\')"}',
            id="json_in_code_block",
        ),
        pytest.param(
            '{"action": "EXECUTE_CODE", "code": "print(\'test\')"}',
            '{"action": "EXECUTE_CODE", "code": "print(\'test\')"}',
            id="plain_json",
        ),
        pytest.param(
            'Some text before ```json\n{"action": "EXECUTE_CODE"}\n``` and after',
            '{"action": "EXECUTE_CODE"}',
            id="json_with_surrounding_text",
        ),
        pytest.param(
            'Text {"action": "EXECUTE_CODE"} more text',
            '{"action": "EXECUTE_CODE"}',
            id="json_embedded_in_text",
        ),
        pytest.param(
            '<think>Thinking...</think>{"action": "EXECUTE_CODE"}',
            '{"action": "EXECUTE_CODE"}',
            id="json_with_think_tags",
        ),
        pytest.param(
            '```json\n{"nested": {"key": "value"}}\n```',
            '{"nested": {"key": "value"}}',
            id="nested_json_in_code_block",
        ),
        pytest.param('{"incomplete": "json"', '{"incomplete": "json"', id="incomplete_json"),
        pytest.param("No JSON content", "No JSON content", id="no_json_content"),
        pytest.param(
            'JSON response content: ```json\n{"action": "WRITE", "learnings": "I learned...", "response": "Writing the first 10 Fibonacci numbers to a markdown file in a readable format.", "code": "", "content": "# First 10 Fibonacci Numbers\\n\\nThe following are the first 10 Fibonacci numbers, starting with F(0) = 0 and F(1) = 1. Each subsequent number is the sum of the two preceding numbers.\\n\\n```\\n0, 1, 1, 2, 3, 5, 8, 13, 21, 34\\n```", "file_path": "fibonacci_numbers.md", "mentioned_files": [], "replacements": []}\n```',  # noqa: E501
            '{"action": "WRITE", "learnings": "I learned...", "response": "Writing the first 10 Fibonacci numbers to a markdown file in a readable format.", "code": "", "content": "# First 10 Fibonacci Numbers\\n\\nThe following are the first 10 Fibonacci numbers, starting with F(0) = 0 and F(1) = 1. Each subsequent number is the sum of the two preceding numbers.\\n\\n```\\n0, 1, 1, 2, 3, 5, 8, 13, 21, 34\\n```", "file_path": "fibonacci_numbers.md", "mentioned_files": [], "replacements": []}',  # noqa: E501
            id="json_response_content_marker",
        ),
    ],
)
def test_clean_json_response(response_content: str, expected_output: str) -> None:
    """Test the clean_json_response function with various inputs.

    Args:
        response_content (str): Input string containing JSON with potential code blocks
        or think tags
        expected_output (str): Expected cleaned JSON output
    """
    assert clean_json_response(response_content) == expected_output
