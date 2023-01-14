---
cover: /embeds/books/engineering-in-plain-sight-an-illustrated-field-guide-to-the-constructed-environment.jpg
date: '2023-01-12'
goodreads_id: 60690050
isbn: 171850232X
isbn13: '9781718502321'
page_count: 251
rating: 5
reviews/authors:
- Grady Hillhouse
reviews/lists:
- 2023 Book Reviews
title: 'Engineering in Plain Sight: An Illustrated Field Guide to the Constructed
  Environment'
---
Well that's a delightful read. I relatively recently came across the [Practical Engineer](https://www.youtube.com/@PracticalEngineeringChannel) YouTube Channel, where he goes into a whole pile of various civil engineering and other infrastructure topics. 

A particular favorite of mine is:

{{<youtube "_OpC4fH3mEk">}}

So when I saw that he had a book... of course I was going to read it! And it's pretty awesome. Topic by topic, he goes into a high level but with some detail on all sorts of ways that infrastructure actually works and neat things you can look out for. 

I certainly learned a lot and I highly recommend checking it out. 

If you'd like to see my various thoughts throughout the book, read on!

<!--more-->

## Electrical Grid

> Unlike other utilities, electricity is quite challenging to store on a large scale, which means power must be generated, transported, supplied, and used all in the same moment. The energy coursing through the wires of your home or office was a ray of sunshine on a solar panel, an atom of uranium, or a bit of coal or natural gas in a steam boiler only milliseconds ago.  

Power storage yo. We're getting there (slowly) with battery technology, but it's still a hard problem. 

> Power is usually generated and transmitted on three individual lines called phases (sometimes labeled A, B, and C), each of which has voltage offset from its neighbors. Creating electricity in three distinct phases provides a smooth supply that overlaps, so there is never a moment when all phases have zero voltage. A three-phase supply also uses fewer equivalent conductors than a single-phase supply to carry the same amount of power, making it more economical. You’ll notice that almost all electrical infrastructure shows up in groups of three, with each conductor or piece of equipment handling an individual phase of the supply.  

I knew it was phased before, but it’s interesting to both know why and to know to keep an eye out for things in threes. I wonder what happens if one of the The is interrupted or damaged. 

> Many of the methods we use to generate power are just different ways of boiling water. Plants that use this method are called thermal power stations because they rely on heat to create steam. The steam passes through a turbine, which is coupled to an AC generator connected to the power grid. The speed of the turbine must be carefully synchronized to the frequency of the rest of the grid.  

It’s interesting how everything from the oldest steam power to nuclear power all relies on water_steam. The renewables tend not to (solar's photoelectric effect and hydro_wind relying on motion rather than heat directly) at least?

> Utility-scale turbines are usually around 1 to 2 megawatts each, but units as large as 10 megawatts have been installed. That’s enough to power about 5,000 households with a single turbine!  

That's a lot of power. And they usually come in large fields. The wind farm between Indianapolis and Chicago produces ~800MW and can power 200k homes [<sup>Source</sup>](https://www.edpr.com/north-america/meadow-lake-wind-farm). That's pretty cool. 

> The theoretical maximum efficiency that can be extracted (called the Betz limit) is about 60 percent. The slender blades of the turbine are carefully designed to capture as much energy as possible without slowing the air stream too much.  

And that's why they don't just use gigantic blades. If you do, the air stacks up. Nothing is perfect/100% in nature. 

> You might think that all the lights [on top of wind turbines] would need to be wired together, but the complexity of such a system would be unreliable and costly. Instead, each light is outfitted with a GPS receiver that gets a highly accurate clock signal from satellites overhead. If each light has its clock synchronized, the flashes will be synchronized as well.  

I never really considered that. GPS is such an amazing technology. Uses more than one would ever expect. 

> The amount of wasted power from resistance is related to the current in the line, so more current means more wastage. If you increase the voltage of the electricity, you need less current to deliver the same amount of power, so that’s exactly what we do. Transformers at power plants boost the voltage before sending electricity on its way over transmission lines, which reduces the current in the lines, minimizes energy wasted due to resistance of the conductors, and ensures that as much power as possible reaches the customers at the other end.  

And that's why. Except those high voltage lines are also extremely dangerous, so they're the larger/taller towers. More than that, because of the high voltage, the distance electricity could jump through the air is higher. 

> Transmission conductors not only need to carry the electricity, but they must also span great distances between each pylon and withstand the forces of wind and weather. They can also become hot when moving a great deal of electrical current. This heat causes the lines to sag as the metal conductors expand.  

Huh. I knew all those parts. But putting all together and realizing that load can cause electrical line to sag is fascinating. 

> Much of the equipment used in outdoor substations is called air insulated switchgear because it uses ambient air and spacing to prevent high-voltage arcs from forming between energized components. Another type of equipment called gas insulated switchgear involves encapsulated equipment in metal enclosures filled with a dense gas called sulfur hexafluoride, which allows installation of high-voltage components in locations where space is limited.  

Rare, but cool. It is the same gas that does the opposite of helium and makes your voice much deeper if your breathe it in. 

> However, fuses are the simplest protective devices. More sophisticated circuit breakers can occasionally be seen, including reclosers, which are usually housed in small cylindrical or rectangular canisters. Reclosers open when a fault is detected, then close again to test whether the fault has cleared. Most faults on the grid are temporary, such as lightning or small tree limbs making contact with energized lines. Reclosers protect transformers without requiring a worker to come replace a fuse for minor issues. They usually trip and reclose a few times before deciding that a fault is permanent and locking out. If you ever lose and regain electricity in a short period of time, a recloser is probably why.  

Well that’s cool! I did wonder. 

## Communications 
> Each landline consists of a twisted pair of thin copper wires. Since every household and business can have its own direct lines to the local telephone exchange, the cables can grow quite large, sometimes containing hundreds or thousands of pairs. The lines join together into larger and larger cables at splices, easily visible by the boxy black splice enclosures seen near poles.  

Huh. I was aware that originally all lines connected to a manual operator / switchboard, but never really connected that with the idea that modern (ish) lines would do the same, just automated, necessitating one line per line. That’s a lot of copper. 

> Moisture is mostly a problem for telephone lines (as opposed to coaxial or fiber-optic cables), because they have so many individual copper wires, and older cables were often insulated using paper. To counteract the intrusion of moisture, many telephone cables are pressurized with air inside the sheath using a compressor near the central telephone office.  

That seems both obvious and crazy. How in the world does it maintain the pressure? Surely it leaks like crazy? Or are they somehow immune to that over time?

> Geostationary satellites also have a much larger range since they have a line of sight that covers about 40 percent of the globe. Only the Earth’s poles are difficult to reach from this orbit.  

That’s neat. I realized that they were far away to get the right orbital period, which in turn increased latency. But I never really considered that they would see significantly more of the Earth that way. 

> Within only a narrow range of frequencies, wireless carriers have innovated ways to connect anyone with a mobile device to both the telephone network and the internet. The fundamental innovation making this possible is the subdivision of large service areas into smaller cells—hence the name, cellular communications.  

You know… I never really considered **why** they were called cell phones. 

## Roadways

> Ever wonder about the difference between speed humps, bumps, and lumps? A speed hump is a tool to slow down vehicles on public roadways and is usually 4 meters (12 feet) in width. A speed bump is smaller in width but taller in height, and is intended for parking lots and garages. Speed lumps (also called cushions) are similar to speed humps, but they have gaps to allow emergency vehicles to pass through without slowing down. These obstacles are unappreciated by motorists, mainly because they are uncomfortable even at the slowest of speeds. Newer designs in development use fluids that harden when drivers go too fast but let slow drivers through without a bump.  

I don’t recall having ever seen one of these lumps. That’s pretty cool though! Ditto for the fluid filled ones. Something non-Newtonian?

## Bridges and Tunnels

> Arch bridges usually need strong abutments at either side to push against that can withstand the extra horizontal loads. Alternatively, a tied arch bridge uses a chord to connect both sides of the arch like a bowstring so it can resist the thrust forces. If each end of the arch sits atop a spindly pier, you can be sure that they are tied together.  

That’s a cool concept. Using the weight on each support to pull against the other in the opposite direction. 

> The other option is to use a tunnel boring machine (TBM). These massive pieces of equipment act like giant drills, using a rotating cutterhead to chew through the rock and soil. TBMs also include conveyors to remove the spoils as they are excavated and equipment to install concrete lining segments that support the tunnel walls and roof. (The next section includes more details on tunnel lining.) Although they are hugely expensive and difficult to transport, these machines can make tunnel construction a rapid and efficient process. They are most often used on long, large-diameter projects or tunnels in very challenging ground conditions.  

That’d be cool to see. Giant machines are neat. Tunnels are neat. But how would you be able to see it working?

## Railways
Trains!

> Locomotives may look huge, but their engines are almost trivial compared to the enormous weight they move. If your car were so efficient, it could run off a tiny string-trimmer engine.  

That’s such an awesome mental model. Love it. 

> Some signals are controlled by a dispatcher, but many operate automatically using track circuits. In the most basic configurations, a low-voltage electric current is introduced into the rails at one end of the block. At the other end, a relay measures the current to control the nearby signals. When a train enters a block, the wheels and axles create a conductive path between the rails, shorting the circuit and de-energizing the relay.  

Well that’s cool. I had no idea it worked automatically as such. 

> On rapid transit, where trains decelerate quickly, regenerative energy comes in short bursts, reducing its usefulness to other trains. However, in areas with many hills, it can be a boon. In an ideal situation, much of the energy a train uses to climb a large hill can be returned to the system as it descends to be used by other trains.  

On a line with connected power lines, one train going down a hill can help power anther going up. That’s so cool. 

## Dams, Levees, and Costal Structures
Dam. 

> If properly sized, a groin can also protect the area on the downdrift side by reducing the speed and power of ocean currents along the shore.  

😆

> Another option for creating revetments and breakwaters is to use cast concrete blocks, often known as armor units. These unique structures are formed in geometric shapes, allowing them to entangle and interlock to resist powerful hydrodynamic forces.  

Those strange looking piles of concrete jacks! Fun to climb on. 

> In the United States, many levees and floodwalls are designed to guard against the 100-year flood, a somewhat confusing term for a simple concept. Because we have extensive historical records of rainfall worldwide, we can estimate the relationship between any storm’s severity and its probability of occurring. The 100-year flood is a reference point on that line: a theoretical storm that has a 1 percent chance of being equaled or exceeded in a given year at a certain location. Although its name implies that it happens only once every hundred years, the 1 percent annual chance equates to a 26 percent chance of such a storm occurring within a 30-year window. Over 50 years, that probability approaches 40 percent, nearly the flip of a coin.  

That’s an interesting way of doing the math that I hadn’t really thought of before. There’s also climate change to consider, but that it’s a statistically interesting problem even without that is neat. People are intuitively bad at statistics. 

## Municipal Water and Waste Water

> Over long periods of time, infiltrating water can accumulate into vast underground resources called aquifers. A common misconception is that groundwater is stored in open areas like underground rivers or lakes. Although they exist in some locations, large underground caverns are relatively rare. Nearly all groundwater aquifers are geologic formations of sand, gravel, or rock that are saturated with water, just like a sponge.  

It makes perfect sense. It’s still a bummer. Vast underground lakes and rivers sound cooler. 

> High-service pumps used in water distribution systems consume significant amounts of electricity, so they often require robust connections to the electrical grid and backup generators for potential outages. Energy is often one of the highest ongoing costs for a water utility.  

That pumps would take power, I get. But so much? Less so. Cool. 

> In large cities, it’s not unusual for buildings to be so tall that the main water pressure cannot deliver water to the top. Most tall buildings have their own system of pumps and tanks to ensure that each floor has adequate water pressure. Some cities require buildings to have a rooftop tank and pump, effectively spreading out the elevated storage across an urban area (rather than having centralized large towers).  

Making use of the height to solve the problem of the pumping at that height. That’s neat. 

## Construction

> Installation of a tower crane is a feat on its own, so they usually are used only for projects with extended durations, like tall buildings. They often have a base of reinforced concrete and require another crane for assembly and disassembly. Some tower cranes can raise themselves, allowing the mast to increase in height as a building is built up from the ground. A climbing frame secures two sections of the mast as they are disconnected, lifting the upper part of the crane. Next, the crane raises and inserts a new mast section into the opening the climbing frame creates, where it is bolted into place. This process can be repeated as many times as needed to reach the desired height.  

The idea of cranes building themselves is amusing. 
