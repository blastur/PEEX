#! /usr/bin/env python
"""Python wEbpage EXchanger

usage: peex [options] <configfile>

options:
-d				Dry run (do not modify destination tree)
-v				Verbosity level (may be used multiple times)
-c				Enable pretty console colors

-u				Update the modification time of destination files instead
				of source files to achieve sync. This is NOT recommended 
				as many FTP server implementations are broken.
"""

import ConfigParser
import getopt
import sys
import os
import re
import time

import tree
import ops

# When enabled, do not modify destination tree
dryrun = False

# Verbosity level
loglevel = 0

# Use pretty colors in output?
colors = False

# Update source "modtime" instead of dest 
srcutime = True

COLOR_PINK = '\033[95m'
COLOR_BLUE = '\033[94m'
COLOR_GREEN = '\033[92m'
COLOR_YELLOW = '\033[93m'
COLOR_RED = '\033[91m'
COLOR_END = '\033[0m'

LOGLEVEL_FATAL = 0
LOGLEVEL_WARNING = 1
LOGLEVEL_DETAILED = 2

WIDTH = 25

class Profile:
	config = { }
	srcmask = []
	dstmask = []

	def __init__(self, filename):
		cfg = ConfigParser.RawConfigParser()
		if (len(cfg.read(filename)) == 0):
			raise IOError
	
		self.config['host'] = cfg.get('site', 'host')
		self.config['user'] = cfg.get('site', 'user')
		self.config['pass'] = cfg.get('site', 'pass')
		self.config['port'] = cfg.getint('site', 'port')
		self.config['source'] = cfg.get('site', 'source')
		self.config['dest'] = cfg.get('site', 'dest')

		try:
			ignore = cfg.items('exceptions')
			for pattern, ptype in ignore:
				if (ptype == 'protect'):
					log(LOGLEVEL_DETAILED, "Compiling remote pattern: " + pattern)
					self.dstmask.append(re.compile(pattern))
				elif (ptype == 'ignore'):
					log(LOGLEVEL_DETAILED, "Compiling local pattern: " + pattern)
					self.srcmask.append(re.compile(pattern))
				else:
					log(LOGLEVEL_WARNING,"warning: unknown patterntype '" + ptype + "', ignoring.")
		except ConfigParser.NoSectionError:
			pass

	def __str__(self):
		return "-- Config\n" + \
			   "Host: " + self.config['host'] + "\n" \
			   "User: " + self.config['user'] + "\n" \
			   "Pass: " + self.config['pass'] + "\n" \
			   "Port: " + str(self.config['port']) + "\n" \
			   "\n" + \
			   "Source directory: " + self.config['source'] + "\n" \
			   "Destination directory: " + self.config['dest'] + "\n" \

def log(level, msg, color = None):
	global loglevel
	
	if (level <= loglevel): 
		if (color is not None and colors):
			print color + msg + COLOR_END
		else:
			print msg

def rmfile(ops, node):
	if not dryrun: ops.rmfile(node.abspath)
	
def rmdir(ops, node):	
	indent = " " * WIDTH * (node.level)

	# remove subdirs (unless protected)
	for d in node.subdirs:
		log(LOGLEVEL_WARNING, indent + d.name.ljust(WIDTH) + "----->", COLOR_PINK)
		rmdir(ops, d)
			
	# remove files
	for f in node.files:
		if not f.ignored:
			log(LOGLEVEL_WARNING, indent + f.name.ljust(WIDTH) + "Removing obsolete file", COLOR_RED)
			rmfile(ops, f)		
		else:
			log(LOGLEVEL_WARNING, indent + f.name.ljust(WIDTH) + "Protecting obsolete file", COLOR_YELLOW)

	
	# remove self
	if not node.ignored:
		log(LOGLEVEL_WARNING, indent + node.name.ljust(WIDTH) + "Removing obsolete file", COLOR_RED)	
		if not dryrun:
			ops.rmdir(node.abspath)
	else:
		log(LOGLEVEL_WARNING, indent + node.name.ljust(WIDTH) + "Protecting obsolete file", COLOR_YELLOW)
	
def mkdir(ops, node):
	if not dryrun: ops.mkdir(node.abspath)
	
def putfile(ops, srcNode, dstNode):
	if not dryrun: 
		ops.putfile(srcNode.abspath, dstNode.abspath)

def setModtime(ops, node):
	if not dryrun:
		ops.utime(node.abspath, node.modtime)

def getModtime(ops, node):
	if dryrun:
		return 0
	else:
		return ops.modtime(node.abspath)	

def syncDir(srcOps, srcNode, dstOps, dstNode):
	indent = " " * WIDTH * (srcNode.level)

	# Put new/changed files
	for sfile in srcNode.files:
		if sfile.ignored:
			log(LOGLEVEL_DETAILED, indent + sfile.relpath.ljust(WIDTH) + "Ignoring file", COLOR_BLUE)
			continue

		doUpload = True
		for dfile in dstNode.files:
			if sfile == dfile:				
				if (sfile.size != dfile.size):
					log(LOGLEVEL_WARNING, indent + sfile.name.ljust(WIDTH) + "Destination filesize differs (" + str(sfile.size) + " vs " + str(dfile.size) + "). Overwriting!", COLOR_GREEN)
#				elif (sfile.modtime != dfile.modtime):
#					log(LOGLEVEL_WARNING, indent + sfile.name.ljust(WIDTH) + "Destination modtime differs (src " + str(sfile.modtime) + " vs dst " + str(dfile.modtime) + "). Overwriting!", COLOR_GREEN)
				else:
					log(LOGLEVEL_DETAILED, indent + sfile.name.ljust(WIDTH) + "Destination file is already up-to-date", COLOR_BLUE)
					doUpload = False
				break

		if doUpload:
			dfile = dstNode.addFile(sfile.name, sfile.size, sfile.modtime)
			log(LOGLEVEL_WARNING, indent + sfile.name.ljust(WIDTH) + "Creating new file", COLOR_GREEN)
			putfile(dstOps, sfile, dfile)
			
			if srcutime:
				# Less correct, more portable
				sfile.modtime = getModtime(dstOps, dfile)
				log(LOGLEVEL_DETAILED, indent + sfile.name.ljust(WIDTH) + "Setting source modtime to " + str(sfile.modtime), COLOR_BLUE)
				setModtime(srcOps, sfile)
			else:
				# More correct, less portable
				dfile.modtime = sfile.modtime
				log(LOGLEVEL_DETAILED, indent + dfile.name.ljust(WIDTH) + "Setting destination modtime to " + str(dfile.modtime), COLOR_BLUE)
				setModtime(dstOps, dfile)
				

	# Remove obsolete files
	for dfile in dstNode.files:
		if not dfile in srcNode.files:
			if not dfile.ignored:
				log(LOGLEVEL_WARNING, indent + dfile.name.ljust(WIDTH) + "Removing obsolete file", COLOR_RED)
				rmfile(dstOps, dfile)
			else:
				log(LOGLEVEL_WARNING, indent + dfile.name.ljust(WIDTH) + "Protecting obsolete file", COLOR_YELLOW)

	# Remove obsolete subdirs
	for ddir in dstNode.subdirs:
		if not ddir in srcNode.subdirs:
			if not ddir.ignored:
				log(LOGLEVEL_WARNING, indent + ddir.relpath.ljust(WIDTH) + "Removing dir", COLOR_RED)
				rmdir(dstOps, ddir)
			else:
				log(LOGLEVEL_WARNING, indent + ddir.relpath.ljust(WIDTH) + "Protecting obsolete dir", COLOR_YELLOW)

	# Create new subdirs
	for sdir in srcNode.subdirs:
		if sdir.ignored:
			log(LOGLEVEL_DETAILED, indent + sdir.relpath.ljust(WIDTH) + "Ignoring source dir", COLOR_BLUE)
			continue
		
		ddir = None
		if not sdir in dstNode.subdirs:
			# Dir is not present in dest tree, create and sync
			log(LOGLEVEL_WARNING, indent + sdir.relpath.ljust(WIDTH) + "Creating missing subdir", COLOR_GREEN)
			ddir = dstNode.addSubdir(sdir.name)
			mkdir(dstOps, ddir)			
		else:
			# Even if its present, we still gotta sync it
			log(LOGLEVEL_DETAILED, indent + sdir.relpath.ljust(WIDTH) + "Already exists, no need to create", COLOR_BLUE)
			for adir in dstNode.subdirs:
				if (sdir == adir):
					ddir = adir
					break;
			
		log(LOGLEVEL_WARNING, indent + sdir.relpath.ljust(WIDTH) + "----->", COLOR_PINK)
		syncDir(srcOps, sdir, dstOps, ddir)	

def sync(srcOps, srcNode, srcMask, dstOps, dstNode, dstMask):
	flagIgnored(srcNode, srcMask)
	flagIgnored(dstNode, dstMask)
	syncDir(srcOps, srcNode, dstOps, dstNode)

def ignoredFile(afile, mask):
	for pattern in mask:
		if pattern.match(afile.relpath):
			return True			
	return False

def flagIgnored(node, mask):
	for sub in node.subdirs:
		flagIgnored(sub, mask)

	for afile in node.files:
		if ignoredFile(afile, mask):
			afile.ignored = True

			# Flag container dir and its parents as ignored
			dir = afile.dir
			while True:
				dir.ignored = True
				dir = dir.parent
				if dir is None:
					break		

def main():
	global loglevel
	global dryrun
	global colors
	global srcutime
	
	try:
		opts, args = getopt.getopt(sys.argv[1:], 'dvcu')
	except getopt.error, msg:
		usage(msg)

	for o, a in opts:
		if o == '-d': dryrun = True
		if o == '-v': loglevel = loglevel + 1
		if o == '-c': colors = True
		if o == '-u': srcutime = False
		
	if not args: 
		usage('error: no config specified')

	try:
		profile = Profile(args)
	except IOError:
		print 'error: invalid config ' + str(args)
		sys.exit(3)

	print profile

	if dryrun:
		print "**************************************************************************"
		print "*** Running in dryrun mode. No changes will be made to the destination ***"
		print "**************************************************************************"

	srcOps = ops.DiskOps()
	dstOps = ops.FTPOps(profile.config['host'], profile.config['port'], profile.config['user'], profile.config['pass'])

	srcRoot = srcOps.list(profile.config['source'])
	dstRoot = dstOps.list(profile.config['dest'])

	if (srcRoot is None):
		print "error: source directory '" + profile.config['source'] + "' does not exist."
		sys.exit(4)

	if (dstRoot is None):
		print "error: destination directory '" + profile.config['dest'] + "' does not exist."
		sys.exit(4)

	sync(srcOps, srcRoot, profile.srcmask, dstOps, dstRoot, profile.dstmask)
	
def usage(*args):
	sys.stdout = sys.stderr
	print __doc__
	for msg in args: print msg
	sys.exit(2)

if __name__ == "__main__":
	main()
