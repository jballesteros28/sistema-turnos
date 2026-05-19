def get_query_initial(request, *field_names):
    initial = {}

    for field_name in field_names:
        value = request.GET.get(field_name, "").strip()
        if value.isdigit():
            initial[field_name] = value

    return initial


def get_query_id(request, field_name):
    value = request.GET.get(field_name, "").strip()
    return value if value.isdigit() else ""
