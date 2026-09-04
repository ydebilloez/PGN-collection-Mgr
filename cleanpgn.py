#!/usr/bin/env python3
"""
cleanpgn.py by Yves De Billoez

Reads a PGN file and removes games that:
- contain 'rapid' or 'blitz' in the Event or EventType tag
- contain 'simul' in the Event or EventType tag
- contain 'U10', 'U12', 'U14', 'U16', 'U17' or 'U18' in
  the Event or EventType tag
- contain 'computer', 'Comp' or 'program' in the player tags

Also correct the following items in the file:
- CRLF is being replaced by LF in output files
- double quotes in tag descriptions Event, WhiteTeam and
  BlackTeam are being replaced by single quotes

Writes kept games to output.pgn, rejected games to rejected.pgn.

Usage:
    python cleanpgn.py input.pgn output.pgn rejected.pgn

SPDX-License-Identifier: GPL-2.0-only
"""

import sys
import re


def get_tag(tags: str, tag_name: str) -> str | None:
    """
    Extract the value of a tag (e.g., Event, EventType) from the game block.
    Handles nested/unquoted quotes inside the value and returns the content
    with all double quotes replaced by single quotes.
    Returns None if the tag is not present.
    """
    # Greedy capture: from the first quote after the tag name to the last quote before ']'
    pattern = rf'\[{tag_name}\s+"(.*)"\]'
    match = re.search(pattern, tags, re.IGNORECASE)
    if match:
        raw_value = match.group(1)
        return raw_value.replace('"', "'")
    return None


def has_invalid_tagtext(tags: str) -> bool:
    """
    Check if FEN tag is present
    Check if the Event or EventType tag contains some predefined values (case-insensitive).
    Check if the player or event is a computer tournament
    """
    fen = get_tag(tags, 'FEN')
    if (fen):
        return True

    event = get_tag(tags, 'Event')
    event_type = get_tag(tags, 'EventType')
    comparestring = r'\b(rapid|blitz|U08|U10|U12|U14|U16|U17|U18|Comp|simul)\b'

    if event and re.search(comparestring, event, re.IGNORECASE):
        return True
    if event_type and re.search(comparestring, event_type, re.IGNORECASE):
        return True

    white = get_tag(tags, 'White')
    black = get_tag(tags, 'Black')
    comparestring = r'(computer|program|Comp )\b'

    if white and re.search(comparestring, white, re.IGNORECASE):
        return True
    if black and re.search(comparestring, black, re.IGNORECASE):
        return True

    return False


def should_keep_game(tags: str, moves: str) -> bool:
    """
    Test if game is to be kept or not
    """
    if has_invalid_tagtext(tags):
        return False

    return True


def fix_tag_quotes(tags: str) -> str:
    """
    Replace double quotes inside the values of Event, WhiteTeam and
    BlackTeam tags with single quotes. Returns the modified tags.
    """
    # Pattern matches tag lines for WhiteTeam or BlackTeam (case-insensitive)
    # Captures:
    #   group(1): leading whitespace + '[' + optional whitespace
    #   group(2): tag name (WhiteTeam or BlackTeam)
    #   group(3): whitespace after tag name
    #   group(4): the value inside the quotes (including any nested quotes)
    #   group(5): trailing whitespace + ']' + whitespace
    pattern = re.compile(
        r'^(\s*\[\s*)(Event|WhiteTeam|BlackTeam)(\s+)"(.*)"(\s*\]\s*)$',
        re.IGNORECASE | re.MULTILINE
    )
    # Helper
    def repl(match):
        new_value = match.group(4).replace('"', "'")
        # Reconstruct the tag line with the modified value
        return (match.group(1) + match.group(2) + match.group(3) +
                '"' + new_value + '"' + match.group(5))

    return re.sub(pattern, repl, tags)


def fix_comments(moves: str) -> str:
    """
    2. Remove all occurrences of '/\' from inside every comment.
    """
    # Helper to process each comment
    def process_comment(match):
        content = match.group(1)
        # Remove "/\" from content
        content = content.replace('/\\', '')
        # Replaces [] braces by () braces inside comment
        content = content.replace('[', '(')
        content = content.replace(']', ')')
        return '{' + content + '}'

    # Find all comments { ... } and process them
    moves = re.sub(r'\{([^}]*)\}', process_comment, moves)
    return moves


def process_game(tags, moves, outfile, rejfile, game_count):
    """
    Fix tags and moves, then write the game to outfile (accepted)
    or rejfile (rejected). Returns updated game_count.
    """
    fixed_tags = fix_tag_quotes(tags)
    fixed_moves = fix_comments(moves)

    if should_keep_game(fixed_tags, fixed_moves):
        # write to outfile
        outfile.write(fixed_tags + '\n\n' + fixed_moves)
        if not fixed_moves.endswith('\n'):
            outfile.write('\n')
    else:
        # write to rejfile
        rejfile.write(fixed_tags + '\n\n' + fixed_moves)
        if not fixed_moves.endswith('\n'):
            rejfile.write('\n')

    game_count += 1
    if game_count % 10000 == 0:
        sys.stdout.write(f"\rGames: {game_count}")
        sys.stdout.flush()

    return game_count


def split_tags_moves(block: str) -> tuple[str, str]:
    """
    Split a game block (string) into tags and movetext using the first
    empty line as separator. Returns (tags_part, movetext_part).
    """
    separator = '\n\n'
    if separator in block:
        tags, moves = block.split(separator, 1)
        moves = moves.lstrip('\n')   # remove leading newlines
        return tags, moves
    else:
        return block, ''


def main():
    if len(sys.argv) != 4:
        print("Usage: python cleanpgn.py input.pgn output.pgn rejected.pgn")
        sys.exit(1)

    in_path, out_path, rej_path = sys.argv[1:]

    try:
        with open(in_path, 'r', encoding='latin-1') as infile, \
             open(out_path, 'w', encoding='latin-1', newline='\n') as outfile, \
             open(rej_path, 'w', encoding='latin-1', newline='\n') as rejfile:

            current_lines = []          # lines of the current game block
            game_count = 0
            prev_line_empty = True      # start of file = after an empty line

            for line in infile:
                stripped = line.strip()

                # Detect start of a new game: '[' after an empty line
                if stripped.startswith('[') and prev_line_empty:
                    # Finalize previous game block (if any)
                    if current_lines:
                        block = ''.join(current_lines)
                        tags, moves = split_tags_moves(block)
                        game_count = process_game(tags, moves, outfile, rejfile, game_count)
                        current_lines = []

                    # Start new block with this tag line
                    current_lines.append(line)
                    prev_line_empty = False
                else:
                    # Append to current block
                    current_lines.append(line)
                    prev_line_empty = (stripped == '')

            # Process the last game
            if current_lines:
                block = ''.join(current_lines)
                tags, moves = split_tags_moves(block)
                game_count = process_game(tags, moves, outfile, rejfile, game_count)

            print(f"\rGames: {game_count}, processing done.")

    except FileNotFoundError:
        print(f"Error: Input file '{in_path}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


# run main only if called directly, not calling it when included
if __name__ == '__main__':
    main()

# eof
