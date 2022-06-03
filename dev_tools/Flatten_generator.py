shape = "G7"


def location2node(location):
    return chr(location[0] + 64 + 1) + str(location[1] + 1)


def node2location(node):
    return ord(node[0]) % 32 - 1, int(node[1]) - 1


shape = node2location(shape.upper())
for y in range(shape[1] + 1):
    text = ", ".join([location2node((x, y)) for x in range(shape[0] + 1)]) + ", \\"
    print(text)
print("    = MAP.flatten()")
