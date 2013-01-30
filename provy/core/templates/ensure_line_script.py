
LINE=""" {{line}} """
LINE = LINE[1:-1]
TARGET="""{{target}}"""

import os

with open(TARGET, 'r') as file:
    append_file = LINE not in file.read()

if append_file:
    with open(TARGET, 'a') as file:
        file.write(LINE)

if not append_file:
    print "0"
else:
    print "1"
