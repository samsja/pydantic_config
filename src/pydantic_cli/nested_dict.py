from pydantic_cli.error import DuplicateKeyError


def merge_nested_dict(left_dict, right_dict):
    """
    this function take two nested dict and merge them together.
    """

    if not isinstance(left_dict, dict) or not isinstance(right_dict, dict):
        raise TypeError("left_dict and right_dict must be dict")

    shared_key = [key for key in left_dict.keys() if key in right_dict.keys()]

    current_dict_non_shared = {
        k: v for k, v in left_dict.items() if k not in shared_key
    }
    new_branch_non_shared = {k: v for k, v in right_dict.items() if k not in shared_key}

    merged_dict = {**current_dict_non_shared, **new_branch_non_shared}

    for key in shared_key:
        if not isinstance(left_dict[key], dict) or not isinstance(
            right_dict[key], dict
        ):
            raise DuplicateKeyError(f"{key} is duplicated")

        merged_dict[key] = merge_nested_dict(left_dict[key], right_dict[key])

    return merged_dict
