# There is a security bug in Rack::Cors where origins * sets allow-credentials to true
# We only want allow-credentials to be true for our own requests, otherwise you need an access token
# Note: Third party subdomains (such as shop/support/blog) should not get cookies in case of XSS
config.middleware.insert_before 0, Rack::Cors do
    allow do
    origins /^(shop|support|blog)\.#{MyWebsite::SESSION_HOST}$/
    resource '*', MyWebsite::CONFIG[:cors_headers].merge({:credentials => false})
    end

    allow do
    origins /(^|\.)#{MyWebsite::SESSION_HOST}$/
    resource '*', MyWebsite::CONFIG[:cors_headers].merge({:credentials => true})
    end

    allow do
    origins /.*/
    resource '*', MyWebsite::CONFIG[:cors_headers].merge({:credentials => false})
    end
end