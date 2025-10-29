from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary or list by key/index."""
    if dictionary is None:
        return None
    try:
        return dictionary[key]
    except (KeyError, IndexError, TypeError):
        return None


@register.simple_tag
def get_branch_errors(validation_errors, is_reference, branch_index):
    """Get errors for a specific branch."""
    if is_reference:
        return validation_errors.get("reference_branch", {})
    treatment_branches = validation_errors.get("treatment_branches", [])
    try:
        return treatment_branches[branch_index]
    except (IndexError, TypeError):
        return {}
