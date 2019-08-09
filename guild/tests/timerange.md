# Time range spec

## Lexer

    >>> from guild.timerange import trlex
    >>> lexer = trlex.lexer()

    >>> def tokens(s):
    ...     lexer.input(s)
    ...     while True:
    ...         tok = lexer.token()
    ...         if not tok:
    ...             break
    ...         print(tok)

    >>> tokens("")

Numbers:

    >>> tokens("1")
    LexToken(NUMBER,1,1,0)

    >>> tokens("2 3 4")
    LexToken(NUMBER,2,1,0)
    LexToken(NUMBER,3,1,2)
    LexToken(NUMBER,4,1,4)

Dates:

    >>> tokens("2019-10-31")
    LexToken(LONGDATE,(2019, 10, 31),1,0)

    >>> tokens("19-11-30")
    LexToken(MEDIUMDATE,(19, 11, 30),1,0)

    >>> tokens("12-31")
    LexToken(SHORTDATE,(12, 31),1,0)

    >>> tokens("9-8")
    LexToken(SHORTDATE,(9, 8),1,0)

    >>> tokens("1-31")
    LexToken(SHORTDATE,(1, 31),1,0)

    >>> tokens("1-32")
    LexToken(SHORTDATE,(1, 32),1,0)

    >>> tokens("2018-13-01")
    LexToken(LONGDATE,(2018, 13, 1),1,0)

Times:

    >>> tokens("11:10")
    LexToken(SHORTTIME,(11, 10),1,0)

    >>> tokens("0:00")
    LexToken(SHORTTIME,(0, 0),1,0)

    >>> tokens("1:00")
    LexToken(SHORTTIME,(1, 0),1,0)

    >>> tokens("1:2")
    Traceback (most recent call last):
    LexError: unexpected ':2' at position 1

    >>> tokens("13:30")
    LexToken(SHORTTIME,(13, 30),1,0)

    >>> tokens("23:59")
    LexToken(SHORTTIME,(23, 59),1,0)

    >>> tokens("24:00")
    LexToken(SHORTTIME,(24, 0),1,0)

    >>> tokens("24:00:00")
    LexToken(LONGTIME,(24, 0, 0),1,0)

    >>> tokens("24:01:02")
    LexToken(LONGTIME,(24, 1, 2),1,0)

    >>> tokens("000:0")
    Traceback (most recent call last):
    LexError: unexpected ':0' at position 3

Units:

    >>> tokens("minutes hours days weeks months years")
    LexToken(MINUTE,'minutes',1,0)
    LexToken(HOUR,'hours',1,8)
    LexToken(DAY,'days',1,14)
    LexToken(WEEK,'weeks',1,19)
    LexToken(MONTH,'months',1,25)
    LexToken(YEAR,'years',1,32)

    >>> tokens("minute hour day week month year")
    LexToken(MINUTE,'minute',1,0)
    LexToken(HOUR,'hour',1,7)
    LexToken(DAY,'day',1,12)
    LexToken(WEEK,'week',1,16)
    LexToken(MONTH,'month',1,21)
    LexToken(YEAR,'year',1,27)

    >>> tokens("MINutes houR DaY WEEKs MONths yeARs")
    LexToken(MINUTE,'MINutes',1,0)
    LexToken(HOUR,'houR',1,8)
    LexToken(DAY,'DaY',1,13)
    LexToken(WEEK,'WEEKs',1,17)
    LexToken(MONTH,'MONths',1,23)
    LexToken(YEAR,'yeARs',1,30)

Variations / abbreviations:

    >>> tokens("min minute minutes")
    LexToken(MINUTE,'min',1,0)
    LexToken(MINUTE,'minute',1,4)
    LexToken(MINUTE,'minutes',1,11)

    >>> tokens("hr hour hours")
    LexToken(HOUR,'hr',1,0)
    LexToken(HOUR,'hour',1,3)
    LexToken(HOUR,'hours',1,8)

Other reserved:

    >>> tokens("today yesterday this last ago before after between and")
    LexToken(TODAY,'today',1,0)
    LexToken(YESTERDAY,'yesterday',1,6)
    LexToken(THIS,'this',1,16)
    LexToken(LAST,'last',1,21)
    LexToken(AGO,'ago',1,26)
    LexToken(BEFORE,'before',1,30)
    LexToken(AFTER,'after',1,37)
    LexToken(BETWEEN,'between',1,43)
    LexToken(AND,'and',1,51)

    >>> tokens("toDaY yesTERday thIS LAsT AGO beFoRE AFTer betWEEn AND")
    LexToken(TODAY,'toDaY',1,0)
    LexToken(YESTERDAY,'yesTERday',1,6)
    LexToken(THIS,'thIS',1,16)
    LexToken(LAST,'LAsT',1,21)
    LexToken(AGO,'AGO',1,26)
    LexToken(BEFORE,'beFoRE',1,30)
    LexToken(AFTER,'AFTer',1,37)
    LexToken(BETWEEN,'betWEEn',1,43)
    LexToken(AND,'AND',1,51)

Expressions:

    >>> tokens("after 5 minutes ago")
    LexToken(AFTER,'after',1,0)
    LexToken(NUMBER,5,1,6)
    LexToken(MINUTE,'minutes',1,8)
    LexToken(AGO,'ago',1,16)

    >>> tokens("before this week")
    LexToken(BEFORE,'before',1,0)
    LexToken(THIS,'this',1,7)
    LexToken(WEEK,'week',1,12)

    >>> tokens("between 1 and 3 hours ago")
    LexToken(BETWEEN,'between',1,0)
    LexToken(NUMBER,1,1,8)
    LexToken(AND,'and',1,10)
    LexToken(NUMBER,3,1,14)
    LexToken(HOUR,'hours',1,16)
    LexToken(AGO,'ago',1,22)

    >>> tokens("between 5-1 and 5-31")
    LexToken(BETWEEN,'between',1,0)
    LexToken(SHORTDATE,(5, 1),1,8)
    LexToken(AND,'and',1,12)
    LexToken(SHORTDATE,(5, 31),1,16)

Invalid:

    >>> tokens("a")
    Traceback (most recent call last):
    LexError: unexpected 'a' at position 0

    >>> tokens("aftr last week")
    Traceback (most recent call last):
    LexError: unexpected 'aftr' at position 0

    >>> tokens("after the equinox")
    Traceback (most recent call last):
    LexError: unexpected 'the' at position 6

    >>> tokens("yearsss")
    Traceback (most recent call last):
    LexError: unexpected 'ss' at position 5

    >>> tokens("2015-01-03-01")
    Traceback (most recent call last):
    LexError: unexpected '-01' at position 10

## Parser

The time range parser generates a function that returns a tuple of
start and end times for a reference time. The function can be used to
implement a filter for a time range by matching times greater than or
equal to start and less than end.

Let's first create a parser:

    >>> from guild.timerange import trparse
    >>> parser = trparse.parser()

Next we'll create a helper function that applies a time range spec to
a reference time and prints the start and end times.

    >>> def apply(s, ref):
    ...     f = parser.parse(s)
    ...     start, end = f(ref)
    ...     print("ref:   %s" % ref)
    ...     print("start: %s" % start)
    ...     print("end:   %s" % end)

Here's a reference date for our core tests:

    >>> from datetime import datetime
    >>> ref = datetime(2019, 5, 1, 14, 35, 23)

### Unit ranges

Unit ranges are specs that imply a range of time that is defined by
a specified unit. Unites include minutes, hours, days, weeks, months,
and years.

Ranges can be specified using special keywords "this" and "last",
indicating the range that falls within the reference time and the
range that occurs just prior to the reference time respectively. For
example, "this hour" indicates that the range should fall within the
reference time hour as defined by the range "00:00" and
"00:59". Similarly, "last hour" secifies the range in the hour prior
to the reference time.

Ranges can also be specified using the syntax "N <unit(s)> ago". For
example, "1 hour ago" specifies the range of one hour occuring prior
to the reference time hour start.

Below are examples applied to our reference time.

Minute ranges:

    >>> apply("this minute", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 14:35:00
    end:   2019-05-01 14:36:00

    >>> apply("1 minute ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 14:34:00
    end:   2019-05-01 14:35:00

    >>> apply("5 minutes ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 14:30:00
    end:   2019-05-01 14:31:00

Hour ranges:

    >>> apply("this hour", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 14:00:00
    end:   2019-05-01 15:00:00

    >>> apply("1 hour ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 13:00:00
    end:   2019-05-01 14:00:00

    >>> apply("5 hours ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 09:00:00
    end:   2019-05-01 10:00:00

    >>> apply("24 hours ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-30 14:00:00
    end:   2019-04-30 15:00:00

Day ranges:

    >>> apply("today", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 00:00:00
    end:   2019-05-02 00:00:00

    >>> apply("yesterday", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-30 00:00:00
    end:   2019-05-01 00:00:00

    >>> apply("1 day ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-30 00:00:00
    end:   2019-05-01 00:00:00

    >>> apply("2 days ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-29 00:00:00
    end:   2019-04-30 00:00:00

    >>> apply("10 days ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-21 00:00:00
    end:   2019-04-22 00:00:00

Week ranges:

    >>> apply("this week", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-29 00:00:00
    end:   2019-05-06 00:00:00

    >>> apply("1 week ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-22 00:00:00
    end:   2019-04-29 00:00:00

    >>> apply("2 weeks ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-15 00:00:00
    end:   2019-04-22 00:00:00

    >>> apply("10 weeks ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-02-18 00:00:00
    end:   2019-02-25 00:00:00

Month ranges:

    >>> apply("this month", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 00:00:00
    end:   2019-05-31 00:00:00

    >>> apply("1 month ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-01 00:00:00
    end:   2019-04-30 00:00:00

    >>> apply("3 months ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-02-01 00:00:00
    end:   2019-02-28 00:00:00

    >>> apply("15 months ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2018-02-01 00:00:00
    end:   2018-02-28 00:00:00

    >>> apply("39 months ago", ref)  # leap year
    ref:   2019-05-01 14:35:23
    start: 2016-02-01 00:00:00
    end:   2016-02-29 00:00:00

Year ranges:

    >>> apply("this year", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-01-01 00:00:00
    end:   2020-01-01 00:00:00

    >>> apply("1 year ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2018-01-01 00:00:00
    end:   2019-01-01 00:00:00

    >>> apply("5 years ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2014-01-01 00:00:00
    end:   2015-01-01 00:00:00

### Operator ranges

Operator ranges apply a "before" or "after" operator to an explicit
time or unit range.

If the operator is "before" and a unit range is specified, the time
range will have no start time and end with the range start time.

If the operator is "after" and a unit range is specified, the time
range will start with the range end time and have no end time.

#### Before operations

Explicit date:

    >>> apply("before 2018-4-29", ref)
    ref:   2019-05-01 14:35:23
    start: None
    end:   2018-04-29 00:00:00

Explicit date and time:

    >>> apply("before 2019-4-29 9:35", ref)
    ref:   2019-05-01 14:35:23
    start: None
    end:   2019-04-29 09:35:00

    >>> apply("before 2019-4-29 9:35:05", ref)
    ref:   2019-05-01 14:35:23
    start: None
    end:   2019-04-29 09:35:05

    >>> apply("before 19-4-29 9:35", ref)
    ref:   2019-05-01 14:35:23
    start: None
    end:   2019-04-29 09:35:00

    >>> apply("before 89-4-1", datetime(1900, 1, 1))
    ref:   1900-01-01 00:00:00
    start: None
    end:   1989-04-01 00:00:00

Short date (ref year applies):

    >>> apply("before 4-29", ref)
    ref:   2019-05-01 14:35:23
    start: None
    end:   2019-04-29 00:00:00

    >>> apply("before 4-29", datetime(1900, 1, 1))
    ref:   1900-01-01 00:00:00
    start: None
    end:   1900-04-29 00:00:00

Short date and time:

    >>> apply("before 4-28 15:45", ref)
    ref:   2019-05-01 14:35:23
    start: None
    end:   2019-04-28 15:45:00

Time only (ref date applies):

    >>> apply("before 23:30", ref)
    ref:   2019-05-01 14:35:23
    start: None
    end:   2019-05-01 23:30:00

    >>> apply("before 23:30", datetime(1989, 3, 28))
    ref:   1989-03-28 00:00:00
    start: None
    end:   1989-03-28 23:30:00

Unit ranges:

    >>> apply("before today", ref)
    ref:   2019-05-01 14:35:23
    start: None
    end:   2019-05-01 00:00:00

    >>> apply("before 10 minutes ago", ref)
    ref:   2019-05-01 14:35:23
    start: None
    end:   2019-05-01 14:25:00

    >>> apply("before 2 days ago", ref)
    ref:   2019-05-01 14:35:23
    start: None
    end:   2019-04-29 00:00:00

#### After operations

Explicit date:

    >>> apply("after 2018-4-29", ref)
    ref:   2019-05-01 14:35:23
    start: 2018-04-29 00:00:00
    end:   None

Explicit date and time:

    >>> apply("after 2019-4-29 9:35", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-29 09:35:00
    end:   None

    >>> apply("after 19-4-29 9:35", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-29 09:35:00
    end:   None

Short date (current year applies):

    >>> apply("after 4-29", ref)
    ref:   2019-05-01 14:35:23
    start: ...-04-29 00:00:00
    end:   None

Short date and time:

    >>> apply("after 4-28 15:45", ref)
    ref:   2019-05-01 14:35:23
    start: ...-04-28 15:45:00
    end:   None

Time only (current date applies):

    >>> apply("after 23:30", ref)
    ref:   2019-05-01 14:35:23
    start: ... 23:30:00
    end:   None

Unit ranges:

    >>> apply("after yesterday", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 00:00:00
    end:   None

    >>> apply("after 1 day ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 00:00:00
    end:   None

    >>> apply("after 12 months ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2018-05-31 00:00:00
    end:   None

### Last N unit ranges

A range can also be specified as `last N UNIT`.

    >>> apply("last 2 minutes", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 14:33:23
    end:   None

    >>> apply("last hour", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 13:35:23
    end:   None

    >>> apply("last 6 hours", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 08:35:23
    end:   None

    >>> apply("last 10 days", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-21 14:35:23
    end:   None

#### Comparing after and last forms

There's an important difference between the `after ... ago` and `last
...` forms.

The `after ... ago` form goes back to the start of the specified unit
and starts the range *after* the specified interval ends. Here's an
example using `5 minutes`:

    >>> apply("after 5 minutes ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 14:31:00
    end:   None

The `last ...` form simply goes back the specified units
without. Here's the same example using `5 minutes`:

    >>> apply("last 5 minutes", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 14:30:23
    end:   None

Consider this distinction for larger intervals such as weeks, months,
and years. Does "1 week ago" mean the start of the previous week
through the end of the same week, or does it mean exactly 7 days (168
hours) ago? By English convention, "1 week ago" unambiguously means
the former. In this light, the expression "after 1 week ago" means to
start after the prior week ended, or, at the start of the current
week.

The distinction therefore can be summarized as:

- `after ... ago` starts after the specified period has ended
- `last N ...` starts precisely N units in the past

To avoid the ambiguity of calculating weeks, months, and years in the
past, the form `last N` cannot be used with those units:

    >>> apply("last 2 weeks", None)
    Traceback (most recent call last):
    ParseError: unexpected 'weeks' at pos 7

    >>> apply("last month", None)
    Traceback (most recent call last):
    ParseError: unexpected 'month' at pos 5

    >>> apply("last 1 year", None)
    Traceback (most recent call last):
    ParseError: unexpected 'year' at pos 7

For these intervals, you must use `after ... ago` - noting again that
the period starts *after* the specified interval.

    >>> apply("after 2 weeks ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-22 00:00:00
    end:   None

    >>> apply("after 1 month ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-30 00:00:00
    end:   None

    >>> apply("after 1 year ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-01-01 00:00:00
    end:   None

When applied to smaller intervals, both forms can be used, but with
different meaning.

Here's `last ...` applied to `3 days`:

    >>> apply("last 3 days", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-28 14:35:23
    end:   None

Note the interval is exactly 3 days prior to the reference date.

Here's `after ... ago` applied to `3 days`:

    >>> apply("after 3 days ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-29 00:00:00
    end:   None

The interval starts *after* the 3rd day ends.

To further explain the rationale for this distinction, consider the
time range expression "3 days ago". In keeping with the example "1
week ago", which means the range "starting on Monday at 00:00 of the
previous week and ending on the following Monday at 00:00 (exclusive),
the expression "3 days ago" means the range "starting at 00:00 three
days in the past and ending at 00:00 on the following day (again,
exslusive).

    >>> apply("3 days ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-28 00:00:00
    end:   2019-04-29 00:00:00

By specifying a range that starts *after* "3 days ago", the range must
start at 00:00 on the following day, as shown above.

### Explicit ranges

An explicit range is specified using the syntax "between TIME_1 and
TIME_2" where `TIME_1` and `TIME_2` are any valid time or unit range.

The times values do not have to be in order.

    >>> apply("between yesterday and today", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-30 00:00:00
    end:   2019-05-02 00:00:00

    >>> apply("between today and yesterday", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-30 00:00:00
    end:   2019-05-02 00:00:00

    >>> apply("between 10 minutes ago and 5 minutes ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 14:25:00
    end:   2019-05-01 14:31:00

    >>> apply("between 1-1 and 1-31", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-01-01 00:00:00
    end:   2019-01-31 00:00:00

    >>> apply("between 1-31 and 1-1", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-01-01 00:00:00
    end:   2019-01-31 00:00:00

    >>> apply("between 0:00 and 12:00", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 00:00:00
    end:   2019-05-01 12:00:00

    >>> apply("between 0:00:05 and 12:00:45", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 00:00:05
    end:   2019-05-01 12:00:45

    >>> apply("between 1-1 0:00:05 and 1-1 12:00:45", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-01-01 00:00:05
    end:   2019-01-01 12:00:45

    >>> apply("between 2018-1-1 and 10 days ago", ref)
    ref:   2019-05-01 14:35:23
    start: 2018-01-01 00:00:00
    end:   2019-04-22 00:00:00

    >>> apply("between 10 days ago and today", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-04-21 00:00:00
    end:   2019-05-02 00:00:00

### Explicit date/time

    >>> apply("10:00", ref)
    ref:   2019-05-01 14:35:23
    start: 2019-05-01 10:00:00
    end:   2019-05-01 10:01:00

    >>> apply("2018-10-31 14:30", ref)
    ref:   2019-05-01 14:35:23
    start: 2018-10-31 14:30:00
    end:   2018-10-31 14:31:00

    >>> apply("2018-10-31 14:30:05", ref)
    ref:   2019-05-01 14:35:23
    start: 2018-10-31 14:30:05
    end:   2018-10-31 14:30:06

    >>> apply("2018-10-31", ref)
    ref:   2019-05-01 14:35:23
    start: 2018-10-31 00:00:00
    end:   2018-11-01 00:00:00

### Invalid dates and time

    >>> apply("before 2018-4-31", None)
    Traceback (most recent call last):
    ValueError: day is out of range for month

    >>> apply("between 11:00 and 24:00", None)
    Traceback (most recent call last):
    ValueError: hour must be in 0..23
