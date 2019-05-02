# --- application.rb

# Force HTTPS + HSTS + secure cookies when behind an ELB
config.middleware.insert_before 0, Rack::SslEnforcer, ignore: lambda { |request| request.env["HTTP_X_FORWARDED_PROTO"].blank? }, :hsts => true
