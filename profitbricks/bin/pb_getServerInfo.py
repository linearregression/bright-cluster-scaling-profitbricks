#!/usr/local/bin/python
# encoding: utf-8
'''
pb_getServerInfo -- get some basic specs of a server

pb_getServerInfo is a tool to collect basic specs os servers in a vDC

It defines methods to collect data of a vDCs servers and print selected data to stdout

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

from profitbricks.client import ProfitBricksService, Datacenter, Server


__all__ = []
__version__ = 0.1
__date__ = '2016-02-23'
__updated__ = '2016-02-23'

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
            login = decoded_cred.split(':',1)
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


def getServerInfo(pbclient=None, dc_id=None):
    ''' gets info of servers of a data center'''
    if pbclient is None:
        raise ValueError("argument 'pbclient' must not be None")
    if dc_id is None:
        raise ValueError("argument 'dc_id' must not be None")
    # list of all found server's info
    server_info = []
    servers = pbclient.list_servers(dc_id,3)
    for server in servers['items']:
        props = server['properties']
        server_vols = server['entities']['volumes']['items']
        n_volumes = len(server_vols)
        total_disk = 0
        for vol in server_vols :
            total_disk += vol['properties']['size']
        server_nics = server['entities']['nics']['items']
        n_nics = len(server_nics)
        macs = [nic['properties']['mac'] for nic in server_nics]
        info = dict(id=server['id'], name=props['name'],cores=props['cores'], ram=props['ram'], disks=n_volumes, storage=total_disk, nics=n_nics, macs=macs, state=server['metadata']['state'], vmstate=props['vmState'])
        server_info.append(info)
    # end for(servers)
    return(server_info)
# end getServerInfo()


def select_where(info=None,select=None, **where):
    if info is None:
        raise ValueError("argument 'info' must not be None")
    if len(info) == 0:
        return []
    if select is None:
        select = info[0].keys()
    server_info = []
    for old_si in info:
#        print("old_si: {}".format(old_si))
        w_matches = all(old_si[wk]==wv for (wk,wv) in where.items())
#        print(" - where: {}".format(w_matches))
        new_si = {k:v for (k,v) in old_si.items() if k in select and w_matches}
#         print(" - new_si: {}".format(new_si))
        if len(new_si) > 0:
            server_info.append(new_si)
    # end for(info)
    return(server_info)
# end select_where()


def main(argv=None): # IGNORE:C0111
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

  Created by Jürgen Buchhammer on %s.
  Copyright 2016 ProfitBricks GmbH. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument('-u', '--user', dest='user', help='the login name')
        parser.add_argument('-p', '--password', dest='password', help='the login password')
        parser.add_argument('-L', '--Login', dest='loginfile', default=None, help='the login file to use')
        parser.add_argument('-d', '--datacenterid', dest='dc_id', required=True, default=None, help='datacenter of the server')
        parser.add_argument('-s', '--serverid', dest='serverid', default=None, help='ID of the server')
        parser.add_argument('-n', '--name', dest='servername', default=None, help='name of the new server')
        parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %(default)s]")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)

        # Process arguments
        args = parser.parse_args()
        global verbose
        verbose = args.verbose

        if verbose > 0:
            print("Verbose mode on")

        (user, password) = getLogin(args.loginfile, args.user, args.password)
        if user is None or password is None:
            raise ValueError("user or password resolved to None")
        pbclient = ProfitBricksService(user, password)
        
        server_info = getServerInfo(pbclient, args.dc_id)
        if verbose > 1:
            print("Server info: {}".format(server_info))
        selects = ['id', 'name', 'state', 'vmstate', 'macs']
        wheres = {'cores':2, 'storage':10}
        wheres = {}
        if args.servername is not None:
            wheres = {'name':args.servername} 
#        new_info = select_where(server_info, selects, cores=2, storage=10)
        new_info = select_where(server_info, selects, **wheres)
        print("INFO: {}".format(new_info))
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception:
        traceback.print_exc()
        sys.stderr.write("\n" + program_name + ":  for help use --help\n")
        return 2

if __name__ == "__main__":
    sys.exit(main())
    