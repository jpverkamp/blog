---
title: Wombat IDE - Help and image bug fixes
date: 2012-04-29 04:55:42
programming/languages:
- Java
- Scheme
series:
- Wombat IDE
---
A new feature: any keyword can now have an associated hyperlink that points to the Chez Scheme API reference for that function. Just click on a function that you want help with and hit F1 on your keyboard. The link will open in your systems default browser. So far only the functions built into Petite Chez Scheme work correctly, I'll be adding the C211 libraries as soon as I write the documentation for it.

Also, a few bug fixes related to images:

* Apparently it hasn't been possible to write JPGs because the API expected them to be `TYPE_ARGB` and I was giving them `TYPE_RGB`. A simple conversion and everything is golden. If only all bug fixes where so easy.
* From the same issue, loading grayscale images was causing problems. In previous versions, it would automatically brighten them when converting to `TYPE_RGB`. Now I'm doing the conversion manually. It's a bit slower, but not really noticeably. Most importantly, it works.
* Finally, I added an error message if an image fails to load.
