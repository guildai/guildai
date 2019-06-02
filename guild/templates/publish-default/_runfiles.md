{% set rows = runfiles|csv_dict_rows -%}

{% if rows -%}
| Path | Type | Size | Modified | MD5 |
| ---- | ---- | ---- | -------- | --- |
{% for row in rows %}{% set link = row.path|runfile_link %}| {% if link %}[{{ row.path }}]({{ link }}){% else %}{{ row.path }}{% endif %} | {{ row.type }} | {{ row.size|file_size }} | {{ row.mtime|utc_date('us') }} | {{ row.md5 }} |
{% endfor %}
[runfiles.csv](runfiles.csv)
{% else -%}
There are no files for this run.
{%- endif %}
