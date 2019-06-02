{% set rows = sourcecode|csv_dict_rows -%}

{% if rows -%}
| Path | Size | Modified | MD5 |
| ---- | ---- | -------- | --- |
{% for row in rows %}| [{{ row.path }}](sourcecode/{{ row.path }}) | {{ row.size|file_size }} | {{ row.mtime|utc_date('us') }} | {{ row.md5 }} |
{% endfor %}
[sourcecode.csv](sourcecode.csv)
{% else -%}
There are no source code files for this run.
{%- endif %}
