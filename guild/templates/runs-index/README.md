# Published runs

| ID | Operation | Started | Time | Status | Label |
| -- | --------- | ------- | ---- | ------ | ----- |
{% for run in runs %}| [{{ run.id|short_id }}]({{ run.id }}/README.md) | {{ run.operation }} | {{ run.started|nbsp }} | {{ run.time|nbsp }} | {{ run.status|nbsp }} | {{ run.label|nbsp }} |
{% endfor %}
