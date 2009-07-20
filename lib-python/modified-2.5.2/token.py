#! /usr/bin/env python

"""Token constants (from "token.h")."""

#  This file is automatically generated; please don't muck it up!
#
#  To update the symbols in this file, 'cd' to the top directory of
#  the python source tree after building the interpreter and run:
#
#    python Lib/token.py

#--start constants--
DEDENT = 6
LPAR = 7
STAR = 16
AMPER = 19
LESS = 20
SLASHEQUAL = 40
NUMBER = 2
RPAR = 8
CIRCUMFLEX = 33
NOTEQUAL = 29
VBAR = 18
BACKQUOTE = 25
DOUBLESTAR = 36
MINUS = 15
DOT = 23
STRING = 3
STAREQUAL = 39
GREATEREQUAL = 31
MINEQUAL = 38
LEFTSHIFTEQUAL = 45
SEMI = 13
CIRCUMFLEXEQUAL = 44
NEWLINE = 4
DOUBLESLASHEQUAL = 49
COLON = 11
PERCENTEQUAL = 41
TILDE = 32
PLUS = 14
ERRORTOKEN = 52
RSQB = 10
EQEQUAL = 28
COMMENT = 53
AMPEREQUAL = 42
RIGHTSHIFT = 35
RBRACE = 27
NT_OFFSET = 256
PERCENT = 24
DOUBLESLASH = 48
DOUBLESTAREQUAL = 47
EQUAL = 22
PLUSEQUAL = 37
AT = 50
SLASH = 17
LESSEQUAL = 30
NL = 54
LSQB = 9
N_TOKENS = 55
RIGHTSHIFTEQUAL = 46
GREATER = 21
LBRACE = 26
INDENT = 5
NAME = 1
VBAREQUAL = 43
LEFTSHIFT = 34
COMMA = 12
ENDMARKER = 0
OP = 51
#--end constants--

tok_name = {}
for _name, _value in globals().items():
    if type(_value) is type(0):
        tok_name[_value] = _name


def ISTERMINAL(x):
    return x < NT_OFFSET

def ISNONTERMINAL(x):
    return x >= NT_OFFSET

def ISEOF(x):
    return x == ENDMARKER


def main(data, outFileName):
    # load the output skeleton from the target:
    try:
        fp = open(outFileName)
    except IOError, err:
        sys.stderr.write("I/O error: %s\n" % str(err))
        sys.exit(2)
    format = fp.read().split("\n")
    fp.close()
    try:
        start = format.index("#--start constants--") + 1
        end = format.index("#--end constants--")
    except ValueError:
        sys.stderr.write("target does not contain format markers")
        sys.exit(3)
    lines = []
    for key, val in data.iteritems():
        lines.append("%s = %d" % (key, val))
    format[start:end] = lines
    try:
        fp = open(outFileName, 'w')
    except IOError, err:
        sys.stderr.write("I/O error: %s\n" % str(err))
        sys.exit(4)
    fp.write("\n".join(format))
    fp.close()


if __name__ == "__main__":
    import os
    import sys
    sys.path.append(os.path.join(os.path.dirname(sys.argv[0]), "../../"))
    try:
        from pypy.interpreter.pyparser import pytoken
        data = pytoken.python_tokens.copy()
        data["N_TOKENS"] = len(data)
        data["NT_OFFSET"] = 256
        main(data, __file__)
    finally:
        sys.path.pop()
