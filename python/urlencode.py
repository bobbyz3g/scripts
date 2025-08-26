#!/usr/bin/env python3

import urllib.parse
import argparse


def main():
	parser = argparse.ArgumentParser(description='URL encode/decode input text')
	parser.add_argument('text', help='Text to encode/decode')
	parser.add_argument('-d', '--decode', action='store_true', help='Decode instead of encode')
	args = parser.parse_args()

	if args.decode:
		result = urllib.parse.unquote(args.text)
	else:
		result = urllib.parse.quote(args.text)

	print(result)


if __name__ == '__main__':
	main()
