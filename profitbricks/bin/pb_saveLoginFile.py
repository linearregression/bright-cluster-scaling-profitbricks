#!/usr/local/bin/python
# encoding: utf-8
'''
pb_saveLoginFile -- save login data to file

pb_saveLoginFile is a tool to save your ProfitBricks login data to a file.
This file can be used by other scripts to avoid providing user name/password
on the command line or in the code.
MAKE SURE, THAT THE FILE IS PROTECTED BY OS PERMISSIONS1


@author:     Jürgen Buchhammer

@copyright:  2016 ProfitBricks GmbH. All rights reserved.

@license:    Apache License 2.0

@contact:    juergen.buchhammer@profitbricks.com
@deffield    updated: Updated
'''

import sys
import os
import traceback

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from base64 import b64encode, b64decode

from profitbricks.client import ProfitBricksService


__all__ = []
__version__ = 0.1
__date__ = '2016-05-09'
__updated__ = '2016-05-09'


class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg

    def __str__(self):
        return self.msg

    def __unicode__(self):
        return self.msg
# end class CLIError


def getLogin(filename, user, passwd):
    '''
    write user/passwd to login file or get them from file.
    This method is not Py3 safe (byte vs. str)
    '''
    if filename is None:
        return (user, passwd)
    if os.path.exists(filename):
        print("Using file {} for Login".format(filename))
        with open(filename, "r") as loginfile:
            encoded_cred = loginfile.read()
#             print("encoded: {}".format(encoded_cred))
            decoded_cred = b64decode(encoded_cred)
            login = decoded_cred.split(':', 1)
            return (login[0], login[1])
    else:
        if user is None or passwd is None:
            raise ValueError("user and password must not be None")
        print("Writing file {} for Login".format(filename))
        with open(filename, "w") as loginfile:
            encoded_cred = b64encode(user+":"+passwd)
#             print("encoded: {}".format(encoded_cred))
            loginfile.write(encoded_cred)
        return (user, passwd)
# end getLogin()


def main(argv=None):
    '''parse command line and write file.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version,
                                                     program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

  Created by J. Buchhammer on %s.
  Copyright 2016 ProfitBricks GmbH. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license,
                                formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument('-u', '--user', dest='user', 
                            required=True, help='the login name')
        parser.add_argument('-p', '--password', dest='password',
                            required=True, help='the login password')
        parser.add_argument('-L', '--Login', dest='loginfile', default=None,
                            required=True, help='the login file to use')
        parser.add_argument('-v', '--verbose', dest="verbose", action="count",
                            help="set verbosity level [default: %(default)s]")
        parser.add_argument('-V', '--version', action='version',
                            version=program_version_message)

        # Process arguments
        args = parser.parse_args()
        global verbose
        verbose = args.verbose

        if verbose > 0:
            print("Verbose mode on")

        (user, password) = getLogin(args.loginfile, args.user, args.password)
        if user is None or password is None:
            raise ValueError("user or password resolved to None")
        print("testing access..")
        pbclient = ProfitBricksService(user, password)
        pbclient.list_locations()

    except KeyboardInterrupt:
        # handle keyboard interrupt #
        return 0
    except Exception:
        traceback.print_exc()
        sys.stderr.write("\n" + program_name + ":  for help use --help\n")
        return 2
# end main()


if __name__ == "__main__":
    sys.exit(main())
