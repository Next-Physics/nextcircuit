import builtins, io
from funcs.db_funcs import append_to_chain_history

###
def create_print_with_logging(chain_id):
    original_print = builtins.print

    def print_and_log(*args, **kwargs):
        # Create a StringIO buffer to capture the output
        buffer = io.StringIO()
        # Use the original print function to write to the buffer
        original_print(*args, file=buffer, **kwargs)
        # Get the content from the buffer
        content = buffer.getvalue()
        buffer.close()
        # Call the original print function to display the output
        original_print(*args, **kwargs)
        # Log the content to the database
        append_to_chain_history(chain_id, content)

    return print_and_log
