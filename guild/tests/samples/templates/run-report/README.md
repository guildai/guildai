# Run Report

## Attributes

| Attribute   | Value                 |
| ---------   | -----                 |
| ID          | {{ run.id }}          |
| Directory   | {{ run.dir }}         |
| Model       | {{ run.model }}       |
| Operation   | {{ run.operation }}   |
| Package     | {{ run.pkg }}         |
| Status      | {{ run.status }}      |
| Marked      | {{ run.marked }}      |
| Started     | {{ run.started }}     |
| Stopped     | {{ run.stopped }}     |
| Command     | {{ run.command }}     |
| Exit Status | {{ run.exit_status }} |

## Environment

```
{{ run|env }}
```
