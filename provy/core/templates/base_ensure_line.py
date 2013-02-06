LINE = """ {{line}} """
LINE = LINE[1:-1]
TARGET = """{{target}}"""

with open(LINE, 'r') as file:
    LINE_CONTENT = file.read()

with open(TARGET, 'r') as file:
    append_file = LINE_CONTENT not in file.read()

if append_file:
    with open(TARGET, 'a') as file:
        file.write("\n")
        file.write(LINE_CONTENT)

if not append_file:
    print "0"
else:
    print "1"
