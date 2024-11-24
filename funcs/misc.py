from funcs.db_funcs import append_to_chain_history


# Factory function to create the custom print function
def create_print_with_logging(chain_id):
    # Save the original print function
    original_print = print

    # Define the new print function
    def print_and_log(*args, **kwargs):
        # Convert all arguments to strings and join them
        content = ' '.join(str(arg) for arg in args)
        # Call the original print function
        original_print(*args, **kwargs)
        # Log the content to the database
        append_to_chain_history(chain_id, content)

    return print_and_log