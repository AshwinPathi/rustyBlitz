# How to use

## Manual mode (requires client to be open)

```
$ python3 rustyBlitz.py -c {champion_name} -r {role}
```

The argparse help should give the rest of the information


## Debug manual mode (does not require client to be open)

Use `--dryrun` to allow the scraper to be run without the client open. Use `--no-cache` to disable the caching mechanism

Example:

```
$ python3 rustyBlitz.py -c {champion_name} -r {role} --dryrun --no-cache
```

This will just print out what runes you would populate without actually populating them