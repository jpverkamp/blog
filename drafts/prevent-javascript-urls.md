Filter javascript: links in JS, Ruby, PHP

# Potential problems: https://github.com/OWASP/railsgoat/issues/228

# Ruby

# Protected: Returns true if return_to is relative path or if the host is on the whitelist.
# - return_to: Path or Absolute URL to redirect to.
def safe_redirect?(return_to)
    # Note: parsed_return_to.relative? doesn't work on scheme relative URLs (//www.edmodo.com), it return true.
    #   They also don't have a scheme. True relative URLs have neither scheme nor host.
    begin
        parsed_return_to = URI.parse(return_to)
        is_relative = parsed_return_to.relative? && parsed_return_to.host.nil?
        is_whitelisted = MyWebsite::CONFIG[:redirect_host_whitelist_set].include?(parsed_return_to.host)
        return is_relative || is_whitelisted
    rescue URI::InvalidURIError
        return false
    end
end

# Go
func filterURL(rawURL string) string {
    parsedURL, err := url.Parse(rawURL)

    if err != nil {
        return "404"
    } else if parsedURL.Scheme == "http" || parsedURL.Scheme == "https" || parsedURL.Scheme == "app" {
        return rawURL
    } else if parsedURL.Scheme == "" && strings.HasPrefix(parsedURL.Path, "/") {
        return rawURL
    } else {
        return "404"
    }
}

# PHP
$parsed_launch_url = parse_url($url);
$is_ssl_app = stripos(trim($parsed_launch_url['scheme']), 'https') === 0 ? true: false;

# Python3
urllib.parse