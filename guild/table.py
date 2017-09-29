import click

COL_SPACING = 2

def out(data, cols, sort=None):
    data = sorted(data, _data_cmp(sort))
    formatted = _format_data(data, cols)
    col_info = _col_info(formatted, cols)
    for item in formatted:
        _item_out(item, cols, col_info)

def _data_cmp(sort):
    if sort is None:
        return lambda _x, _y: 0
    else:
        return lambda x, y: _item_cmp(x, y, sort)

def _item_cmp(x, y, sort):
    if isinstance(sort, str):
        return _val_cmp(x, y, sort)
    else:
        for part in sort:
            part_cmp = _val_cmp(x, y, part)
            if part_cmp != 0:
                return part_cmp
        return 0

def _val_cmp(x, y, sort):
    if sort.startswith("-"):
        sort = sort[1:]
        return -cmp(x.get(sort), y.get(sort))
    else:
        return cmp(x.get(sort), y.get(sort))
        
def _format_data(data, cols):
    formatted = []
    for item0 in data:
        item = {}
        formatted.append(item)
        for col in cols:
            item[col] = str(item0.get(col, ""))
    return formatted
        
def _col_info(data, cols):
    info = {}
    for item in data:
        for col in cols:
            coli = info.setdefault(col, {})
            coli["width"] = max(coli.get("width", 0), len(item[col]))
    return info

def _item_out(item, cols, col_info):
    for i, col in enumerate(cols):
        val = item[col]
        last_col = i == len(cols) - 1
        padded = _pad_col_val(val, col, col_info) if not last_col else val
        click.echo(padded, nl=False)
    click.echo("")

def _pad_col_val(val, col, col_info):
    return val.ljust(col_info[col]["width"] + COL_SPACING)
