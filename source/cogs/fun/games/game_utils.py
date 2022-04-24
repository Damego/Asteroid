def spread_to_rows(components: list, max_in_row: int = 5):
    _components = []
    _row = []
    for component in components:
        _row.append(component)

        if len(_row) == max_in_row:
            _components.append(_row)
            _row = []

    return _components
