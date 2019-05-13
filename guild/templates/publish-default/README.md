[Published runs](../README.md)

# {{ run|op_desc }}

| ID                | Operation         | Started           | Duration                     | Status           | Label           |
| --                | ---------         | ---------         | --------                     | ------           | -----           |
| {{ run.short_id}} | {{ run|op_desc }} | {{ run.started }} | {{ run.duration|safe_cell }} | {{ run.status }} | {{ run.label }} |

## Flags

{% include "_flags.md" %}

## Scalars

{% include "_scalars.md" %}

## Files

{% include "_files.md" %}

## Images

{% include "_images.md" %}

## Source

{% include "_source.md" %}

## Attributes

{% include "_run_attrs.md" %}
