# Parsing run filters

Parsing runs filters is handled by `guild.filter`. These tests
demonstrate the expected behavior of the lexer and parsing APIs.

## Lexer tests

    >>> from guild import filter
    >>> lexer = filter.lexer()

    >>> def tokenize(s):
    ...     lexer.input(s)
    ...     for t in lexer:
    ...         print(t)

    >>> tokenize("")

    >>> tokenize("a")
    LexToken(ID,'a',1,0)

    >>> tokenize("'a'")
    LexToken(STR_LITERAL,'a',1,0)

    >>> tokenize("\"a\"")
    LexToken(STR_LITERAL,'a',1,0)

    >>> tokenize("123")
    LexToken(NUMBER,123,1,0)

    >>> tokenize("1.23")
    LexToken(NUMBER,1.23,1,0)

    >>> tokenize(".23")
    LexToken(NUMBER,0.23,1,0)

    >>> tokenize("=")
    LexToken(EQ,'=',1,0)

    >>> tokenize("!=")
    LexToken(NEQ,'!=',1,0)

    >>> tokenize("<>")
    LexToken(NEQ,'<>',1,0)

    >>> tokenize("<")
    LexToken(LT,'<',1,0)

    >>> tokenize("<=")
    LexToken(LTE,'<=',1,0)

    >>> tokenize(">")
    LexToken(GT,'>',1,0)

    >>> tokenize(">=")
    LexToken(GTE,'>=',1,0)

    >>> tokenize("contains")
    LexToken(CONTAINS,'contains',1,0)

    >>> tokenize("a contains 'hello'")
    LexToken(ID,'a',1,0)
    LexToken(CONTAINS,'contains',1,2)
    LexToken(STR_LITERAL,'hello',1,11)

    >>> tokenize("a not contains 'hello'")
    LexToken(ID,'a',1,0)
    LexToken(NOT,'not',1,2)
    LexToken(CONTAINS,'contains',1,6)
    LexToken(STR_LITERAL,'hello',1,15)

    >>> tokenize("and")
    LexToken(AND,'and',1,0)

    >>> tokenize("And")
    LexToken(AND,'And',1,0)

    >>> tokenize("AND")
    LexToken(AND,'AND',1,0)

    >>> tokenize("or")
    LexToken(OR,'or',1,0)

    >>> tokenize("oR")
    LexToken(OR,'oR',1,0)

    >>> tokenize("true")
    LexToken(TRUE,'true',1,0)

    >>> tokenize("True")
    LexToken(TRUE,'True',1,0)

    >>> tokenize("fAlse")
    LexToken(FALSE,'fAlse',1,0)

    >>> tokenize("false")
    LexToken(FALSE,'false',1,0)

    >>> tokenize("not")
    LexToken(NOT,'not',1,0)

    >>> tokenize("is")
    LexToken(IS,'is',1,0)

    >>> tokenize("undefined")
    LexToken(UNDEFINED,'undefined',1,0)

    >>> tokenize("(")
    LexToken(LPAREN,'(',1,0)

    >>> tokenize(")")
    LexToken(RPAREN,')',1,0)

    >>> tokenize("[")
    LexToken(LBRACKET,'[',1,0)

    >>> tokenize("]")
    LexToken(RBRACKET,']',1,0)

    >>> tokenize("in")
    LexToken(IN,'in',1,0)

    >>> tokenize("not")
    LexToken(NOT,'not',1,0)

    >>> tokenize(",")
    LexToken(COMMA,',',1,0)

    >>> tokenize("a,b,c")
    LexToken(ID,'a',1,0)
    LexToken(COMMA,',',1,1)
    LexToken(ID,'b',1,2)
    LexToken(COMMA,',',1,3)
    LexToken(ID,'c',1,4)

    >>> tokenize("'a, b, c'")
    LexToken(STR_LITERAL,'a, b, c',1,0)

    >>> tokenize("\"a, b, c\"")
    LexToken(STR_LITERAL,'a, b, c',1,0)

    >>> tokenize("(a,b,c)")
    LexToken(LPAREN,'(',1,0)
    LexToken(ID,'a',1,1)
    LexToken(COMMA,',',1,2)
    LexToken(ID,'b',1,3)
    LexToken(COMMA,',',1,4)
    LexToken(ID,'c',1,5)
    LexToken(RPAREN,')',1,6)

    >>> tokenize("a=1.2")
    LexToken(ID,'a',1,0)
    LexToken(EQ,'=',1,1)
    LexToken(NUMBER,1.2,1,2)

    >>> tokenize("a='1.2'")
    LexToken(ID,'a',1,0)
    LexToken(EQ,'=',1,1)
    LexToken(STR_LITERAL,'1.2',1,2)

    >>> tokenize("a >= 1.2")
    LexToken(ID,'a',1,0)
    LexToken(GTE,'>=',1,2)
    LexToken(NUMBER,1.2,1,5)

    >>> tokenize("(a = 'foo' or a = 'bar') and b <= 12")
    LexToken(LPAREN,'(',1,0)
    LexToken(ID,'a',1,1)
    LexToken(EQ,'=',1,3)
    LexToken(STR_LITERAL,'foo',1,5)
    LexToken(OR,'or',1,11)
    LexToken(ID,'a',1,14)
    LexToken(EQ,'=',1,16)
    LexToken(STR_LITERAL,'bar',1,18)
    LexToken(RPAREN,')',1,23)
    LexToken(AND,'and',1,25)
    LexToken(ID,'b',1,29)
    LexToken(LTE,'<=',1,31)
    LexToken(NUMBER,12,1,34)

    >>> tokenize("a in (red, green, blue)")
    LexToken(ID,'a',1,0)
    LexToken(IN,'in',1,2)
    LexToken(LPAREN,'(',1,5)
    LexToken(ID,'red',1,6)
    LexToken(COMMA,',',1,9)
    LexToken(ID,'green',1,11)
    LexToken(COMMA,',',1,16)
    LexToken(ID,'blue',1,18)
    LexToken(RPAREN,')',1,22)

    >>> tokenize("a in [red, green, blue]")
    LexToken(ID,'a',1,0)
    LexToken(IN,'in',1,2)
    LexToken(LBRACKET,'[',1,5)
    LexToken(ID,'red',1,6)
    LexToken(COMMA,',',1,9)
    LexToken(ID,'green',1,11)
    LexToken(COMMA,',',1,16)
    LexToken(ID,'blue',1,18)
    LexToken(RBRACKET,']',1,22)

## Parser tests

Create a parser.

    >>> parser = filter.parser()

Helpers:

    >>> def parse(expr):
    ...     print(repr(parser.parse(expr)))

    >>> def test(expr, run):
    ...     return parser.parse(expr)(run)

Empty expressions are invalid.

    >>> parse("")
    Traceback (most recent call last):
    SyntaxError: Syntax error at EOF

Parsing a filter expression returns a function that can be used to
test a run. The function returns True if the run is accepted
(filtered).

### Simple terms

    >>> parse("1")
    <guild.filter.Term 1>

    >>> test("1", None)
    1

    >>> parse("0")
    <guild.filter.Term 0>

    >>> test("0", None)
    0

    >>> parse("1.2")
    <guild.filter.Term 1.2>

    >>> test("1.2", None)
    1.2

    >>> parse("a")
    <guild.filter.Term 'a'>

    >>> test("a", None)
    'a'

    >>> parse("'a'")
    <guild.filter.Term 'a'>

    >>> test("'a'", None)
    'a'

    >>> parse("'1.2'")
    <guild.filter.Term '1.2'>

    >>> test("'1.2'", None)
    '1.2'

    >>> parse("true")
    <guild.filter.Term True>

    >>> test("true", None)
    True

    >>> parse("falSE")
    <guild.filter.Term False>

    >>> test("false", None)
    False

    >>> parse("undefined")
    <guild.filter.Term None>

    >>> print(test("undefined", None))
    None

    >>> parse("[1]")
    <guild.filter.List [1]>

    >>> parse("[1, 2]")
    <guild.filter.List [1, 2]>

    >>> parse("[red]")
    <guild.filter.List ['red']>

    >>> parse("[red,green,blue]")
    <guild.filter.List ['red', 'green', 'blue']>

    >>> parse("[red, blue, 1,1.23]")
    <guild.filter.List ['red', 'blue', 1, 1.23]>

### Run tests

Provide an implemented of `filter.FilterRun`.

    >>> class FilterRun:
    ...     attrs = {
    ...         "id": "abcd1234",
    ...         "started": 1661354455107621,
    ...         "label": "hello world a=1",
    ...         "l": [1, "two", 3.0]
    ...     }
    ...     flags = {
    ...         "a": 1,
    ...         "b": 1.2,
    ...         "c": "red",
    ...         "d": True,
    ...         "id": "4321dcba"
    ...     }
    ...     scalars = {
    ...         "x": 0.456,
    ...         "y": 1.123,
    ...         "b": 1.3
    ...     }
    ...
    ...     def get_attr(self, name):
    ...         return self.attrs.get(name)
    ...
    ...     def get_flag(self, name):
    ...         return self.flags.get(name)
    ...
    ...     def get_scalar(self, key):
    ...         try:
    ...             return {"last_val": self.scalars[key]}
    ...         except KeyError:
    ...             return None

Test run:

    >>> run = FilterRun()

#### Numeric comparison

    >>> parse("a = 1")
    <guild.filter.RunTest a=1>

    >>> test("a = 1", run)
    True

    >>> test("a = 2", run)
    False

    >>> test("a < 1", run)
    False

    >>> test("a <= 1", run)
    True

    >>> test("a > 1", run)
    False

    >>> test("a >= 1", run)
    True

    >>> test("a != 1", run)
    False

    >>> test("a <> 2", run)
    True

    >>> test("b < 1.21", run)
    True

    >>> test("x = 0.456", run)
    True

    >>> test("x < 0.5", run)
    True

#### Tests for undefined

    >>> parse("a is undefined")
    <guild.filter.RunTest a is None>

    >>> test("a is undefined", run)
    False

    >>> parse("a is not undefined")
    <guild.filter.RunTest a is not None>

    >>> test("a is not undefined", run)
    True

    >>> parse("not a is undefined")
    <guild.filter.UnaryOp not a is None>

    >>> test("not a is undefined", run)
    True

#### Non-existing flags

    >>> test("e = 1", run)
    False

    >>> test("e is undefined", run)
    True

    >>> test("e is not undefined", run)
    False

#### Check for membership

    >>> parse("c in ['red',green,blue]")
    <guild.filter.In c in ['red', 'green', 'blue']>

    >>> test("c in [red,green, blue]", run)
    True

    >>> test("c in [green,blue]", run)
    False

    >>> parse("c not in [red, green, blue]")
    <guild.filter.In c not in ['red', 'green', 'blue']>

    >>> test("c not in [red, green, blue]", run)
    False

    >>> test("c not in [green, blue]", run)
    True

#### Contains

    >>> parse("c contains 'ed'")
    <guild.filter.Contains c contains 'ed'>

    >>> parse("c contains ed")
    <guild.filter.Contains c contains 'ed'>

    >>> test("c contains 'ed'", run)
    True

    >>> test("c contains ed", run)
    True

    >>> test("c contains red", run)
    True

    >>> test("c contains fred", run)
    False

    >>> test("c not contains ed", run)
    False

    >>> test("c not contains fred", run)
    True

    >>> test("label contains hello", run)
    True

    >>> test("label contains 'hello world'", run)
    True

    >>> test("label contains 'HELLO WORLD'", run)
    True

    >>> test("xxx contains abc", run)
    False

    >>> test("xxx not contains abc", run)
    True

    >>> test("l contains two", run)
    True

    >>> test("l contains TWO", run)
    False

    >>> test("l contains 1", run)
    True

    >>> test("l contains three", run)
    False

    >>> test("l contains 3", run)
    True

    >>> test("l contains 3.0", run)
    True

#### Logic operations

And:

    >>> parse("a = 1 and b = 1.2")
    <guild.filter.InfixOp a=1 and b=1.2>

    >>> test("a = 1 and b = 1.2", run)
    True

    >>> test("a = 1 and b = 1.3", run)
    False

Or:

    >>> test("true or false", run)
    True

    >>> parse("a = 1 or b = 1.3")
    <guild.filter.InfixOp a=1 or b=1.3>

    >>> test("a = 1 or b = 1.3", run)
    True

    >>> test("a = 1.1 or b = 1.3", run)
    False

Not:

    >>> parse("not true")
    <guild.filter.UnaryOp not True>

    >>> test("not true", run)
    False

    >>> test("not 1", run)
    False

    >>> test("not 0", run)
    True

    >>> test("not a = 1", run)
    False

Mixed expressions:

    >>> test("true or false and true", run)
    True

    >>> test("true or false and false", run)
    True

    >>> True or False and False
    True

    >>> test("(true or false) and false", run)
    False

    >>> test("a = 1 or a = 2 and c in [blue,green]", run)
    True

    >>> test("(a = 1 or a = 2) and c in [blue,green]", run)
    False

    >>> test("not ((a = 1 or a = 2) and c in [blue,green])", run)
    True

    >>> test("a = 1 and b = 1.2", run)
    True

    >>> test("a = 1 and b < 1.2", run)
    False

    >>> test("a = 1 and b <= 1.2", run)
    True

#### Value reference order of predeance

Unless a run value reference is specified with a prefix, run values
are resolved using, in order of precedance, attributes, flags, and
scalars.

    >>> test("id = abcd1234", run)
    True

    >>> test("id = '4321dcba'", run)
    False

    >>> test("b = 1.2", run)
    True

    >>> test("b = 1.3", run)
    False

Using explicit prefixes:

    >>> test("flag:id = '4321dcba'", run)
    True

    >>> test("flag:id = abcd1234", run)
    False

    >>> test("scalar:b = 1.3", run)
    True

    >>> test("scalar:b = 1.2", run)
    False

### Syntax errors

Some sample syntax errors:

    >>> parse("'")
    Traceback (most recent call last):
    SyntaxError: Syntax error at line 1, pos 0: unexpected character '''

    >>> parse("a == 123")
    Traceback (most recent call last):
    SyntaxError: Syntax error at line 1, pos 3: unexpected token '='

    >>> parse("'a' = 123")
    Traceback (most recent call last):
    SyntaxError: Syntax error at line 1, pos 4: unexpected token '='

    >>> parse("a = 1 or \nb(")
    Traceback (most recent call last):
    SyntaxError: Syntax error at line 2, pos 11: unexpected token '('
