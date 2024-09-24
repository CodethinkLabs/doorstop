#!/usr/bin/env python3

import argparse
import doorstop
import os
import subprocess
import sys
import tempfile

""" A script to review Doorstop items and add extra fields: confidence
level and optional comments. """

parser = argparse.ArgumentParser(
                    prog='review',
                    description='Reviews Doorstop items and adds confidence and comment fields')

parser.add_argument('itemname', help="Name of item to review e.g. TS1")
parser.add_argument('-c', '--confidence', help="Specify the level of confidence (0.0-1.0)", type=float)
parser.add_argument('-m', '--comment', help="Specify comment text (will overwrite)")

args = parser.parse_args()

tree = doorstop.build()

def is_valid_confidence(n):
    return n>=0.0 and n<=1.0


try:
    item = tree.find_item(args.itemname)
except doorstop.common.DoorstopError as e:
    print(e)
    sys.exit(1)

print(f"Found {item}")

existing_comment = item.get("review-comments")

if args.comment:
    # replace comment with it
    item.set("review-comments", args.comment)
    print(f"Setting comment on {args.itemname} to CLI-supplied value")
else:
    editor = os.getenv("EDITOR")
    if editor is None:
        print("Warning: The EDITOR environment variable is not set. " +
              "If you want to add a comment, set EDITOR to a text editor and re-run " +
              "this command, or use the -m option")
    else:
        fd, path = tempfile.mkstemp()
        try:
            if existing_comment:
                # Edit or replace
                with os.fdopen(fd, 'w') as tmpfile:
                    tmpfile.write(existing_comment.strip())
                    tmpfile.write("\n")
            else:
                with os.fdopen(fd, 'w') as tmpfile:
                    tmpfile.write(f"Add your comment on {item} here.")
                    tmpfile.write("\n")

            # Spawn editor
            subprocess.run([editor, path])

            with open(path, 'r') as tmpfile:
                new_comment = tmpfile.read()
            item.set("review-comments", new_comment)
        finally:
            os.remove(path)

# now prompt for a confidence level
existing_confidence = item.get("confidence")

if existing_confidence is None:
    existing_confidence = 0

if args.confidence:
    if is_valid_confidence(args.confidence):
        new_confidence_int = args.confidence
    else:
        print(f"Error: Supplied confidence level {args.confidence} is not in the range 0.0 to 1.0.")
        sys.exit(3)
else:
    while True:
        print(f"\nPlease enter your confidence level (in %) that {item}'s sub-requirements are sufficient to satisfy item {item}.")

        new_confidence_text = input(f"Please enter a number between 0 and 1 inclusive. (Default: {existing_confidence}):")

        if new_confidence_text == "":
            new_confidence_int = existing_confidence
            break
        try:
            new_confidence_int = float(new_confidence_text)
        except Exception as e:
            print(f"Can't interpret that value as a number.")
            continue

        if is_valid_confidence(new_confidence_int):
            break
        else:
            print(f"Please enter a number between 0 and 1.")

print(f"Setting new confidence value of {new_confidence_int} to {item}")
item.set("confidence", new_confidence_int)

print(f"Setting {item} as reviewed.")
item.review()
