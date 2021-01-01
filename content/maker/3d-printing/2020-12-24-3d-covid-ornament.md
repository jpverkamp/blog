---
title: 3D COVID-19 Ornament
date: 2020-12-24
---
So. This was actually what I originally intended to make when I made the [2d ornaments]({{< ref "2020-12-22-2d-covid-ornament" >}}):

{{< figure src="/embeds/maker/covid-ornaments/3d/tinkercad-final.png" >}}

Full 3D coronavirus! 

Unfortunately, what I kept getting was something more like this:

{{< figure src="/embeds/maker/covid-ornaments/3d/covid-failure.jpg" >}}

No matter how I tweaked the support settings, I could not get the little knobs to print. I even tried printing it in halves, but only half of it came out still. So it goes. Perhaps next year. [^never] Eesh that's a terrible picture too. 

Links:

* [Original STL model](/embeds/maker/covid-ornaments/3d/covid-3d.stl) ([original source](https://www.thingiverse.com/thing:4166787), licensed under CC BY-NC)[^licenses]
* [With hangler](/embeds/maker/covid-ornaments/3d/covid-3d-with-hanger.stl)
* [With hanger and year](/embeds/maker/covid-ornaments/3d/covid-3d-with-hanger-and-year.stl)
* [Fusion 360 file](/embeds/maker/covid-ornaments/3d/covid-ornament.f3d)
* [Tinkercad file](https://www.tinkercad.com/things/lytsxfSYEEd-stunning-bigery-albar)

<!--more-->

So this one was tricky. I actually tried to use [Fusion 360](https://www.autodesk.com/products/fusion-360/overview) for this. It's more powerful and as I mentioned [once upon a time]({{< ref "2020-02-22-sock-and-underwear-drawer" >}}), I still prefer offline tools for things like this. But coming straight into it and trying to modify an existing STL (which is what the model is) went... poorly. I've since learned more how to convert between solid shapes and STLs (and understand the differences better). But man did it go weird. 

I did mange to add the hanger though, and I'm pretty proud of that. Essentially what I did (I'll start trying videos or better screenshots at some point):

* Create a sketch facing the front of the object
* Create a tall skinny rectangle
* Extrude it back into into a square (from the top)
* Create another sketch on the front face
* In the second sketch, place two concentric circles, centered on the rectangle
* Extrude the outer one as a solid
* Then extrude the inner one as a hole, cutting through both the rectangle and the first circle
* Add fillets everywhere

One of the weird bits I found with Fusion 360 was that if you want to export something that has an STL in it, their default export functionality is ... cloud based for some reason? That's very very weird. It works, but it's also very slow. If you just have a simple part, you can export just pieces locally as an STL with no cloud functionality which makes it all the weirder.

In any case, after having the hanger, I still wanted to put the year on it. So... how in the world do I make a solid cut into an STL in Fusion 360? I haven't figured it out yet. I actually went back to Tinkercad... 

* Export the STL in Fusion 360
* Upload that to Tinkercad
* Add a rectangle cut out
* Export that as an STL
* Re-import the STL, add the 2020 text
* Export again, slice, print

... I know right? But I couldn't figure out how to order those so I could cut the rectangle and then add the text in the same file. It's ... I just don't know. But I did get [the model I wanted]((/embeds/maker/covid-ornaments/3d/covid-3d-with-hanger-and-year.stl)) in the end. It just took a while.

And then I couldn't get the silly thing to print anyways. 

Such is life. 

I may come back to this one, but for now I'm happy with the 2D ones. Onwards!

[^never]: Perhaps never. 

[^licenses]: Licenses are a mess sometimes. The same person (so far as I can tell) uploaded this file to [MyMiniFactory](https://www.myminifactory.com/object/3d-print-coronavirus-2019-ncov-112215) and [Thingiverse](https://www.thingiverse.com/thing:4166787)... under different licenses. The former is BY-NC-ND (which would not allow this derivative work), while the latter is BY-NC (which does). 