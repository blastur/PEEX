#! /usr/bin/env python
import re
import ftplib
import os
import time
import calendar 

import tree

class TreeOps:
	isLocal = True
	
	""" Builds the file tree. All times must be "unixtime" and UTC """
	def list(self, rootpath): return NotImplemented
	
	""" Creates a new directory """
	def mkdir(self, path): return NotImplemented
	
	""" Removes an empty directory """
	def rmdir(self, path): return NotImplemented
	
	""" Puts a file into the tree """
	def putfile(self, srcpath, dstpath): return NotImplemented
	
	""" Removes a file from the tree """
	def rmfile(self, path): return NotImplemented
	
	""" Sets modification time of path (epoch is UTC) """
	def utime(self, path, epoch): return NotImplemented
	
	""" Gets modification time of path (Unix timestamp UTC) """
	def modtime(self, path): return NotImplemented
	
class FTPOps(TreeOps):
	def __init__(self, host, port, user, pwd):
		self.dirpat = re.compile("(.+);\s+(.+)")
		self.factpat = re.compile("(.+?)=(.+?);")
		self.isLocal = False
		self.ftp = ftplib.FTP()
		self.ftp.connect(host, port)
		self.ftp.login(user, pwd)
		#self.ftp.set_debuglevel(2)

	def mdtm(self, filename):
		'''Retrieve the modification time of a file in the format YYYYMMDDHHMMSS.'''
		# Note that the RFC doesn't say anything about 'MDTM'
		resp = self.ftp.sendcmd('MDTM ' + filename)
		if resp[:3] == '213':
			s = resp[3:].strip()
			# workaround for broken FTP servers returning responses
			# starting with e.g. 19104... instead of 2004...
			if len(s) == 15 and s[:2] == '19':
				return repr(1900 + int(s[2:5])) + s[5:]
			return s
	
	def ls(self, node, ftp):	
		raw = []
		self.ftp.retrlines("MLSD " + node.abspath, raw.append)
		for line in raw:
			dirm = self.dirpat.match(line)
			if not dirm:
				print "warning: unrecognized directory listing '" + line + "'"
				continue
				
			factstr = dirm.group(1)
			relname = dirm.group(2)

			if (relname == '.' or relname == '..'):
				continue
			
			facts = self.factpat.findall(factstr)
			if not facts:
				print "warning: unrecognized facts in directory listing '" + factstr + "'"
				continue

			modtime = None
			size = None
			isDir = None
			
			for fname, fval in facts:
				fname = fname.upper()
				if (fname == "SIZE"): size = int(fval)
				elif (fname == "MODIFY"): 
					modtime = time.mktime(time.strptime(fval, "%Y%m%d%H%M%S"))					
				elif (fname == "TYPE"): 
					if (fval.upper() == "FILE"):
						isDir = False
					else:
						isDir = True

			if (isDir):
				subnode = node.addSubdir(relname)
				self.ls(subnode, ftp)                                 
			else:
				if (size is None or modtime is None):
					print "warning: failed to parse required facts in directory listing '" + factstr + "'"
					continue
				node.addFile(relname, size, modtime)
								
	def list(self, rootpath):
		root = tree.TreeDirectory(None, '', rootpath)
		self.ls(root, self.ftp)
		return root		

	def mkdir(self, path):
		self.ftp.mkd(path)
		
	def putfile(self, srcpath, dstpath):
		f = open(srcpath, 'rb')
		self.ftp.storbinary("STOR " + dstpath, f)
		f.close()

	def rmdir(self, path):
		self.ftp.rmd(path)
		
	def rmfile(self, path):
		self.ftp.delete(path)
		
	def utime(self, path, epoch): 
		# self.ftp.voidcmd("MFMT " + str(int(time)) + " " + path)
		timestr = time.strftime("%Y%m%d%H%M%S", time.gmtime(epoch))
		# UTIME is broken on pre 1.0.27 PureFTPD, it sets localtime when given UTC
		self.ftp.voidcmd("SITE UTIME " + path + " " + timestr + " " + timestr + " " + timestr + " UTC")
		
	def modtime(self, path):
		timestr = self.mdtm(path)
		epoch = calendar.timegm(time.strptime(timestr, "%Y%m%d%H%M%S"))
		return epoch

class DiskOps(TreeOps):
	def __init__(self):
		self.isLocal = True

	def dir(self, node):
		for relname in os.listdir(node.abspath):
			fullname = os.path.join(node.abspath, relname)
		
			if (os.path.isfile(fullname)):
				size = os.path.getsize(fullname)
				modtime = os.path.getmtime(fullname)
				node.addFile(relname, size, modtime)
			elif (os.path.isdir(fullname)):
				subnode = node.addSubdir(relname)
				self.dir(subnode)

	def list(self, rootpath):	
		root = tree.TreeDirectory(None, '', rootpath)
		self.dir(root)
		return root

	def utime(self, path, epoch):
		os.utime(path, (epoch, epoch))

