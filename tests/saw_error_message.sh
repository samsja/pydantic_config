# use this file from the root folder. Use it to visualize all error messages

echo "### new line"
uv run python tests/ui_testing.py --no-hello l --a
echo "### new line"
uv run python tests/ui_testing.py hello
echo "### new line"
 uv run python tests/ui_testing.py --no-hello world

