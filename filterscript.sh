#!/bin/bash
#
# script for cleaning list of all games
# developed by Yves De Billoez
#
# SPDX-License-Identifier: GPL-2.0-only
#

# get basename without extension
filename="${1%.*}"

if [ ! -f "seniors.pgn" ]; then
echo "Remove remove blitz, rapid, simul, computer and <U18 games"
python3 cleanpgn.py $1 $filename-seniors.pgn $filename-blitz-rapid-computer.pgn
fi

if [ ! -f "$filename-correctresults.pgn" ]; then
    echo "Create file without bad results, at least 4 ply: $filename-correctresults.pgn"
    cat << EOI > tagfile.rc
Result <> "*"
EOI
    rm -f $filename-correctresults.pgn
    rm -f $filename-badresults.pgn
    ../pgn-extract/pgn-extract -s $filename-seniors.pgn \
        --nobadresults --fixresulttags \
        -l$filename-badresults.log \
        -ttagfile.rc \
        --nosetuptags --fixtagstrings \
        -pl4 \
        --detag Source \
        --detag SourceDate \
        --output $filename-correctresults.pgn -n$filename-badresults.pgn
    rm -f tagfile.rc
fi

if [ ! -f "$filename-noelo-matches.pgn" ]; then
    echo "Create file without easy draws (<6 moves, draw): $filename-noelo-matches.pgn"
    rm -f $filename-short-matches.pgn
    rm -f $filename-noelo-matches.pgn
    ../pgn-extract/pgn-extract -s $filename-correctresults.pgn \
        -pl12 \
        -l$filename-noelo-matches.log \
        --output $filename-noelo-matches.pgn -n$filename-short-matches.pgn
fi

# helper function

split_by_elo_group() {
    cat << EOI > tagfile.rc
Elo >= "$1"
EOI
    echo "Create file with players with at least $1 elo"
    ../pgn-extract/pgn-extract -s "$2" \
        -ttagfile.rc \
        -L$filename-above.log \
        --output $filename-above${1}.pgn -n$filename-below${1}.pgn
    rm -f "$2"
    mv $filename-below${1}.pgn "$2"
    rm -f tagfile.rc
}

# end split_by_elo_group

groups=(100 1800 1900 2000 2100 2200 2300 2400 2500)
start_file="$filename-noelo-matches.pgn"
for gr in "${groups[@]}"; do
    split_by_elo_group "$gr" "$start_file"
    start_file="$filename-above${gr}.pgn"
done

#eof