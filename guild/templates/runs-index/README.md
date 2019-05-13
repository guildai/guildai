# Published runs

| Id | Operation | Started | Duration | Status | Label |
| -- | --------- | ------- | -------- | ------ | ----- |
{% for run in runs %}| [{{ run.short_id }}]({{ run.id }}/README.md) | {{ run|op_desc }} | {{ run.started }} | {{ run.duration }} | {{ run.status }} | {{ run.label }} |
{% endfor %}
