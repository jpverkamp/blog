#!/usr/bin/env python3

import argparse
import boto3
import getpass

from twisted.internet import reactor, defer
from twisted.names import client, dns, error, server

# https://twistedmatrix.com/documents/15.2.1/names/howto/custom-server.html

parser = argparse.ArgumentParser(description = 'Create custom DNS entries for AWS entities')
parser.add_argument('--region', default = 'us-west-2', help = 'AWS region to look up instances in')
parser.add_argument('--port', type = int, default = 10053, help = 'The port to serve the DNS')
parser.add_argument('--ttl', type = int, default = 60, help = 'The default TTL')
parser.add_argument('--debug', action = 'store_true', help = 'Enable debug mode')
args = parser.parse_args()

session = boto3.session.Session(region_name = args.region)
if not session.get_credentials():
    key = input('AWS access key: ')
    secret = getpass.getpass('    AWS secret: ')
    session = boto3.session.Session(aws_access_key_id = key, aws_secret_access_key = secret, region_name = args.region)

class AwsEc2Resolver(object):
    '''Map EC2 server names to DNS entries.'''

    def _useThisResolver(self, name):
        '''Only check hostnames ending with .ec2.aws'''

        return name.endswith('.ec2.aws')

    def _resolve(self, name):
        '''Resolve the given query into answer, authority, and additional sections.'''

        server_name = '*{}*'.format(name.rsplit('.', 2)[0])
        ec2 = session.resource('ec2')
        filters = [
            {'Name': 'tag:Name', 'Values': [server_name]},
            {'Name': 'instance-state-name', 'Values': ['running']},
        ]

        answer = [
            dns.RRHeader(name = name, payload = dns.Record_A(address = instance.private_ip_address, ttl = args.ttl))
            for instance in ec2.instances.filter(Filters = filters)
        ]

        authority = additional = []

        if args.debug: print('response:', [answer, authority, additional])
        return answer, authority, additional

    def query(self, query, timeout = None):
        '''Check if we should use this resolver, otherwise fallback.'''

        name = query.name.name.decode()

        if self._useThisResolver(name):
            if args.debug: print('query:', query)
            return defer.succeed(self._resolve(name))
        else:
            return defer.fail(error.DomainError())

if __name__ == '__main__':
    factory = server.DNSServerFactory(
        clients = [
            AwsEc2Resolver(),
            client.Resolver(resolv = '/etc/resolv.conf')
        ]
    )

    protocol = dns.DNSDatagramProtocol(controller = factory)

    reactor.listenUDP(args.port, protocol)
    reactor.listenTCP(args.port, factory)

    print('Starting DNS server on port {}'.format(args.port))
    reactor.run()