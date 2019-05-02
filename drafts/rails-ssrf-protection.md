# Rails, force SSRF protection with gem

gem 'ssrf_filter', '~> 1.0'

require 'ssrf_filter'

SsrfFilter.get(self.uri)

# Throws exception