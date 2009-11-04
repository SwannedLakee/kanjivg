# -*- coding: utf-8 -*-
#
#  Copyright (C) 2009  Alexandre Courbot
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
from xml.etree.ElementTree import XMLID, tostring
import re, codecs, os, string, kanjivg, os.path

def findText(elt):
	if elt.text: return elt.text
	else:
		childs = elt.getchildren()
		if len(childs): return findText(childs[0])
		else: return None

class Parser:
	def __init__(self, content):
		self.content = content

	def parse(self):
		while 1:
			match = re.search('\$\$(\w*)', self.content)
			if not match: break
			fname = 'callback_' + match.group(1)
			if hasattr(self, fname):
				rfunc = getattr(self, fname)
				ret = rfunc()
				self.content = self.content[:match.start(0)] + ret + self.content[match.end(0):]
			else: self.content = self.content[:match.start(0)] + self.content[match.end(0):]

class TemplateParser(Parser):
	def __init__(self, content, kanji, document, groups):
		Parser.__init__(self, content)
		self.kanji = kanji
		self.document = document
		self.groups = groups

	def callback_kanji(self):
		return self.kanji

	def callback_strokenumbers(self):
		if not self.groups.has_key("StrokeNumbers"):
			print "Error - no StrokeNumbers group for kanji %s (%s)" % (self.kanji, hex(kanjivg.realord(self.kanji)))
			return ""
		numbers = self.groups["StrokeNumbers"]
		elts = numbers.findall(".//{http://www.w3.org/2000/svg}text")
		strs = []
		for elt in elts:
			transform = None
			if elt.attrib.has_key("transform"): transform = elt.attrib["transform"]
			strs.append('<text transform="%s">%s</text>' % (transform, findText(elt)))
		return "\n\t\t".join(strs)

	def callback_strokepaths(self):
		if not self.groups.has_key("StrokePaths"):
			print "Error - no StrokePaths group for kanji %s (%s)" % (self.kanji, hex(kanjivg.realord(self.kanji)))
			return ""
		paths = self.groups["StrokePaths"]
		elts = paths.findall(".//{http://www.w3.org/2000/svg}path")
		strs = []
		for elt in elts:
			d = elt.attrib["d"]
			d = re.sub('(\d) (\d)', '\\1,\\2', d)
			d = re.sub("[\n\t ]+", "", d)
			strs.append('<path d="%s"/>' % (d,))
		return "\n\t\t".join(strs)

for f in os.listdir("SVG"):
	if not f.endswith(".svg"): continue
	if f[4] in "0123456789abcdef":
		kanji = kanjivg.realchr(int(f[:5], 16))
	else: kanji = kanjivg.realchr(int(f[:4], 16))

	document, groups = XMLID(open(os.path.join("SVG", f)).read())
	tpp = TemplateParser(open("template.svg").read(), kanji, document, groups)
	tpp.parse()
	out = codecs.open(os.path.join("newSVG", f), "w", "utf-8")
	out.write(tpp.content)