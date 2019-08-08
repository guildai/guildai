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
    LexToken(DATETIME,(2019, 10, 31),1,0)

    >>> tokens("19-11-30")
    LexToken(DATETIME,(2019, 11, 30),1,0)

    >>> tokens("12-31")
    LexToken(DATETIME,(20..., 12, 31),1,0)

    >>> tokens("9-8")
    LexToken(DATETIME,(20..., 9, 8),1,0)

    >>> tokens("1-31")
    LexToken(DATETIME,(2019, 1, 31),1,0)

    >>> tokens("1-32")
    Traceback (most recent call last):
    ValueError: invalid date '1-32'

    >>> tokens("2018-13-01")
    Traceback (most recent call last):
    ValueError: invalid date '2018-13-01'

Times:

    >>> tokens("11:10")
    LexToken(TIME,(11, 10),1,0)

    >>> tokens("0:00")
    LexToken(TIME,(0, 0),1,0)

    >>> tokens("1:00")
    LexToken(TIME,(1, 0),1,0)

    >>> tokens("1:2")
    LexToken(TIME,(1, 2),1,0)

    >>> tokens("13:30")
    LexToken(TIME,(13, 30),1,0)

    >>> tokens("23:59")
    LexToken(TIME,(23, 59),1,0)

    >>> tokens("24:00")
    Traceback (most recent call last):
    ValueError: invalid time '24:00'

    >>> tokens("000:0")
    Traceback (most recent call last):
    ValueError: invalid time '000:0'

Units:

    >>> tokens("minutes hours days weeks months years")
    LexToken(MINUTES,'minutes',1,0)
    LexToken(HOURS,'hours',1,8)
    LexToken(DAYS,'days',1,14)
    LexToken(WEEKS,'weeks',1,19)
    LexToken(MONTHS,'months',1,25)
    LexToken(YEARS,'years',1,32)

    >>> tokens("minute hour day week month year")
    LexToken(MINUTES,'minute',1,0)
    LexToken(HOURS,'hour',1,7)
    LexToken(DAYS,'day',1,12)
    LexToken(WEEKS,'week',1,16)
    LexToken(MONTHS,'month',1,21)
    LexToken(YEARS,'year',1,27)

    >>> tokens("MINutes houR DaY WEEKs MONths yeARs")
    LexToken(MINUTES,'MINutes',1,0)
    LexToken(HOURS,'houR',1,8)
    LexToken(DAYS,'DaY',1,13)
    LexToken(WEEKS,'WEEKs',1,17)
    LexToken(MONTHS,'MONths',1,23)
    LexToken(YEARS,'yeARs',1,30)

Other reserved:

    >>> tokens("today yesterday this ago before after between and")
    LexToken(TODAY,'today',1,0)
    LexToken(YESTERDAY,'yesterday',1,6)
    LexToken(THIS,'this',1,16)
    LexToken(AGO,'ago',1,21)
    LexToken(BEFORE,'before',1,25)
    LexToken(AFTER,'after',1,32)
    LexToken(BETWEEN,'between',1,38)
    LexToken(AND,'and',1,46)

    >>> tokens("toDaY yesTERday thIS AGO beFoRE AFTer betWEEn AND")
    LexToken(TODAY,'toDaY',1,0)
    LexToken(YESTERDAY,'yesTERday',1,6)
    LexToken(THIS,'thIS',1,16)
    LexToken(AGO,'AGO',1,21)
    LexToken(BEFORE,'beFoRE',1,25)
    LexToken(AFTER,'AFTer',1,32)
    LexToken(BETWEEN,'betWEEn',1,38)
    LexToken(AND,'AND',1,46)

Expressions:

    >>> tokens("after 5 minutes ago")
    LexToken(AFTER,'after',1,0)
    LexToken(NUMBER,5,1,6)
    LexToken(MINUTES,'minutes',1,8)
    LexToken(AGO,'ago',1,16)

    >>> tokens("before this week")
    LexToken(BEFORE,'before',1,0)
    LexToken(THIS,'this',1,7)
    LexToken(WEEKS,'week',1,12)

    >>> tokens("between 1 and 3 hours ago")
    LexToken(BETWEEN,'between',1,0)
    LexToken(NUMBER,1,1,8)
    LexToken(AND,'and',1,10)
    LexToken(NUMBER,3,1,14)
    LexToken(HOURS,'hours',1,16)
    LexToken(AGO,'ago',1,22)

    >>> tokens("between 5-1 and 5-31")
    LexToken(BETWEEN,'between',1,0)
    LexToken(DATETIME,(20..., 5, 1),1,8)
    LexToken(AND,'and',1,12)
    LexToken(DATETIME,(20..., 5, 31),1,16)

Invalid:

    >>> tokens("a")
    Traceback (most recent call last):
    SyntaxError: unexpected 'a' at position 0

    >>> tokens("aftr last week")
    Traceback (most recent call last):
    SyntaxError: unexpected 'aftr' at position 0

    >>> tokens("after the equinox")
    Traceback (most recent call last):
    SyntaxError: unexpected 'the' at position 6

    >>> tokens("yearsss")
    Traceback (most recent call last):
    SyntaxError: unexpected 'ss' at position 5

    >>> tokens("2015-01-03-01")
    Traceback (most recent call last):
    SyntaxError: unexpected '-01' at position 10
