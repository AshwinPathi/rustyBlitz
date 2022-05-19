# QT Gui based blitz.gg clone

## How to build the exe

**Pyinstaller must be run through a windows command prompt and not through WSL. First set up a python environment in windows, install the requirements, and then run the rest of the readme.**

First:
```
$pyi-makespec rustyBlitzGui.py
```

Then change the `datas` directory in `rustyBlitzGui.spec` to map local files to files in use by the executable. Also modify the `console` variable in the `exe` section to be `False`.

Then run:
```
pyinstaller rustyBlitzGui.spec
```

This will create a folder called `dist` which contains the exe. You can run the exe from there.

## Output:
![example](example.png?raw=true)
