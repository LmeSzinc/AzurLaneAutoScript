import re

from dev_tools.slpp import slpp

"""
This file is used to extract `word_template.lua`, aka, the blacklist words file.

Git clone the repository here, https://github.com/Dimbreath/AzurLaneData, to get the decrypted scripts.
Then put your filepath here, like `<your_folder>/<server>/sharecfg/word_template.lua`
Server list: en-US, ja-JP, ko-KR, zh-CN, zh-TW
"""
file = ""
count = 0
with open(file, "r", encoding="utf-8") as f:
    text = f.read()


def extract(dic, word_list):
    """
    Args:
        dic (dict):
        word_list (list[str]):
    """
    global count
    for word, data in dic.items():
        word = str(word)
        if data.get("this", False):
            new = word_list + [word]
            new = "".join(new)
            count += 1
            print(new)
        else:
            new = word_list + [word]
            extract(data, word_list=new)


# CN server
for result in re.findall("word_template = (.*?)return", text, re.DOTALL):
    pg = slpp.decode(result)
    extract(pg, word_list=[])
# Other server
for result in re.findall("uv0\.{0,1}(.*?)end", text, re.DOTALL):
    pg = slpp.decode("{%s}" % result)
    extract(pg, word_list=[])

print(f"Total count: {count}")
