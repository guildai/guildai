from os import mkdir
from os import symlink
from os.path import join as path

from guild.util import touch

touch("a")
touch("b")
mkdir("c")
touch(path("c", "d.txt"))
touch(path("c", "e.txt"))
touch(path("c", "f.bin"))
symlink("c", "l")
touch(path(".guild", "attrs", "exit_status"))
touch(path(".guild", "some-guild-file"))
