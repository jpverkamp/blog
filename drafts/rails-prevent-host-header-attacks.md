# --- application.rb

# Properly set the default URL if we have one to set
# This will avoid attacks where a user sends invalid/multiple host headers   
config.action_controller.default_url_options ||= {}
config.action_controller.default_url_options[:host] ||= MyWebsite::ROOT_URL.split("/")[-1] if MyWebsite::ROOT_URL

# --- config/environments/test.rb
Rails.application.configure do
    ...

  Rails.application.routes.default_url_options = {:host => 'test.host' }
end

# This must be duplicated here to work for tests... :eliphino: 
# https://github.com/rspec/rspec-rails/issues/1275#issuecomment-249609283
Rails.application.routes.default_url_options = {:host => 'test.host' }
