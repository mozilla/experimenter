# blank lines...


def generate_changed_values(
    old_serialized_vals,
    new_serialized_vals,
    latest_change,
    changed_data,
    form_fields=None,
):
    changed_values = {}

    # account for changes in variant values
    if latest_change:
        if old_serialized_vals["variants"] != new_serialized_vals["variants"]:
            old_value = old_serialized_vals["variants"]
            new_value = new_serialized_vals["variants"]
            display_name = "Branches"
            changed_values["variants"] = {
                "old_value": old_value,
                "new_value": new_value,
                "display_name": display_name,
            }

    elif new_serialized_vals.get("variants"):
        old_value = None
        new_value = new_serialized_vals["variants"]
        display_name = "Branches"
        changed_values["variants"] = {
            "old_value": old_value,
            "new_value": new_value,
            "display_name": display_name,
        }

    if changed_data:
        if latest_change:

            for field in changed_data:
                old_val = None
                new_val = None

                if field in old_serialized_vals:
                    if field in ("countries", "locales"):
                        old_field_values = old_serialized_vals[field]
                        codes = [obj["code"] for obj in old_field_values]
                        old_val = codes
                    else:
                        old_val = old_serialized_vals[field]
                if field in new_serialized_vals:
                    if field in ("countries", "locales"):
                        new_field_values = new_serialized_vals[field]
                        codes = [obj["code"] for obj in new_field_values]
                        new_val = codes
                    else:
                        new_val = new_serialized_vals[field]

                display_name = _get_display_name(field, form_fields)

                if new_val != old_val:
                    changed_values[field] = {
                        "old_value": old_val,
                        "new_value": new_val,
                        "display_name": display_name,
                    }

        else:
            for field in changed_data:
                old_val = None
                new_val = None
                if field in new_serialized_vals:
                    if field in ("countries", "locales"):
                        new_field_values = new_serialized_vals[field]
                        codes = [obj["code"] for obj in new_field_values]
                        new_val = codes
                    else:
                        new_val = new_serialized_vals[field]
                    display_name = _get_display_name(field, form_fields)
                    changed_values[field] = {
                        "old_value": old_val,
                        "new_value": new_val,
                        "display_name": display_name,
                    }
    return changed_values


def _get_display_name(field, form_fields):
    if form_fields and form_fields[field].label:
        return form_fields[field].label
    return field.replace("_", " ").title()
