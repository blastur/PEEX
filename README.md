# PEEX
Python wEbpage EXchanger (PEEX) is a non-interactive FTP client for updating
webpages. PEEX is an utility designed to automate the task of remotely
maintaining a web page or other FTP archives. It will synchronize a set of
local files to a remote server by performing uploads and remote deletes as
required. PEEX is heavily inspired by Weex with the important difference that
PEEX does not try to cache remote directory structures locally. This makes it
more cooperative with alien files introduces by 3rd parties. It also enables
multiple developers to collaborate more efficiently.

Main features:
 * Synchronizes a local set of files with a remote FTP server.
 * May be configured to ignore local or remote dirs and files using regular
   expressions.
 * Easy configuration using per-site configuration files.
 * Testrun your configuration using the dry-run option. In this mode PEEX will
   only list scheduled operations but not act on them.

For more details, visit https://github.com/blastur/PEEX

## Installation

Install using pip:
```
$ pip install .
```

If you prefer installing it for your user only, pass the --user argument to pip.

Once installed, PEEX is available on the PATH by running _peex_.

## Configuration
PEEX is configured partly through commandline switches and partly through
config files. The config files contain per-project settings and the command
line switches controls more general options.

Run PEEX without any arguments to show available commandline switches and its
descriptions.

Once the configuration file is setup, synchronization is started by issuing:

	$ peex mysite.peex

It is recommended to set restrictive file permissions on your PEEX configs as
they contain sensitive account details. E.g.

	$ chmod u=rw,o=-rw,g=-rw mysite.peex

For a little bit more details on progress, use:

	$ peex -v mysite.peex

For colored output use:

	$ peex -c -v mysite.peex

where
	Green indicates new files being added to destination tree.
	Red indicates obsolete files in dest (scheduled for removal).
	Blue indicates local files being ignored.
	Yellow indicates destination files being protected.
	Pink indicates current directory in traversal.

### Configuration fileformat (one per project):
```
[site]
host=<ftp_host>
port=<ftp_port>
user=<ftp_user>
pass=<ftp_pass>
source=<source directory on local disk e.g. /home/user/myfiles/>
dest=<destination directory on FTP e.g. /www_files/>

[exceptions]
<regex_pattern>=[ignore|protect]
```

The exceptions section lists files which should either be protected on the
server, or ignored in the local tree. PEEX will never overwrite a protected
remote file nor will it attempt to delete it due to not existing in the local
tree.

Example patterns:
```
[exceptions]
# Do not delete any remote files or dirs CONTAINING the word "uploads"
uploads=protect

# Ignore local files or dirs whos name matches "offline" EXACTLY
^offline$=ignore

# Ignore single file with filename extension
b1\.jpg=protect
```

## Requirements

PEEX will only work with FTP servers that support the MLSD (machine-friendly
list-directory) and SITE UTIME (changing remote file modification time). proFTPd
is known to support both and is recommended when working with PEEX, but many
other FTP server implementation should work aswell.

If your FTP server does not support the required commands, PEEX will stop and
print and an error message.

## Testing

This section is mostly for development / testing purposes. At the moment, PEEX
does not implement any unittests so testing is done manually by running profiles
against a real FTP server. A proFTPd docker container is suitable if you're not
already running a local FTP server.

```
docker run -d --net host -e FTP_USERNAME=test -e FTP_PASSWORD=test -v ~/foo:/home/test hauptmedia/proftpd
```

And the corresponding [site]-block in your profile would look something like
this:
```
[site]
host=localhost
port=21
user=test
pass=test
source=/path/to/test-files/
dest=/
```

This would sync files from /path/to/test-files/ into /home/test in the Docker
container, which is mapped to ~/foo. E.g, PEEX will synchronize two local files
through a proFTPd container.
