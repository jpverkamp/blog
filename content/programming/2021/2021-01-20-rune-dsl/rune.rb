Dir["./components/*.rb"].sort.each { |file| require file }

r = eval(ARGF.read)

#puts r
#puts
puts r.to_xml
