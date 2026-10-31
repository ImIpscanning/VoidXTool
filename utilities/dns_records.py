import dns.resolver as dns
from dns.exception import DNSException, Timeout

class GetDNSRecords:
    def __init__(self, domain):
        '''
Initialize the GetDNSRecords with the domain to look up DNS records.

:param domain: The domain for which the DNS records are being fetched
'''
        self.domain = domain
        self.dns_records_to_look_up = [
            'A',
            'AAAA',
            'CNAME',
            'MX',
            'NS',
            'PTR',
            'SOA',
            'SRV',
            'TXT',
            'CAA',
            'SPF',
            'NAPTR',
            'DNSKEY',
            'DS',
            'TLSA',
            'CERT'
        ]

    def get_dns_records(self):
        '''
Method to get the DNS records of a domain.

:return: The DNS records of the domain
'''
        records = []
        for record_type in self.dns_records_to_look_up:
            try:
                answers = dns.resolver.resolve(self.domain, record_type)
                for rdata in answers:
                    records.append({'type': record_type, 'value': str(rdata)})
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers, Timeout, DNSException):
                continue
        return records