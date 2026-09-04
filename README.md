PGN-collection-Mgr
==================

This is a PGN (Portable Game Notation) manager that allows to
take a basis PGN file with games in it and process it so
that low quality games are partially being filtered out.

One can modify the script to obtain other results.

This project was born as the existing tool `pgn-extract` is
difficult to manage and to extend and did not fit exactly
the target.

### Copyright

Copyright 2026 by Yves De Billoez released under
GNU - GPL v2.0 license.

<!-- SPDX-License-Identifier: GPL-2.0-only -->

You are allowed to copy, modify, extend, fork, ...
whatever is allowed under the above licence.

### Usage

``` bash
./filterscript.sh mylibrary.pgn
```

This will leave the input file unaltered and will create
the following files:

```
mylibrary-noelo-matches.pgn
mylibrary-blitz-rapid-computer.pgn
mylibrary-badresults.pgn
...
mylibrary-above100.pgn
mylibrary-above1800.pgn
...
mylibrary-above2500.pgn
```

Output files can be deleted and the tool can be run again
and again.

### Installation

1. Download or fork or clone or unzip.
2. Make sure the bash script has execute rights.
   Run `chmod +x filterscript.sh` once after downloading.
3. Make sure the pgn-extract tool in installed alongside using
   following structure:
   ```
   ./project/PGN-collection-Mgr/
   ./project/pgn-extract/
   ```

That's all folks.

### Dependencies

- bash
- pgn-extract
- python 3

### Included files

```
.gitignore
cleanpgn.py
filterscript.sh
GPL.md
README.md (this file)
```

_eof_

