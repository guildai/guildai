# Published runs

| ID | Operation | Started | Duration | Status | Label |
| -- | --------- | ------- | -------- | ------ | ----- |
{% for run in runs %}| [{{ run.id|short_id }}]({{ run.id }}/README.md) | {{ run.operation }} | {{ run.started|nbsp }} | {{ run.duration|nbsp }} | {{ run.status|nbsp }} | {{ run.label|nbsp }} |
{% endfor %}
