$('[data-fancybox="gallery"]').fancybox({
  caption: function (instance, item) {
    var caption = $(this).data("caption") || "";

    if (item.type === "image") {
      caption =
        '<a href="' +
        item.opts.flickr +
        '">' +
        caption +
        ' <span class="flickrLink">flickr</span></a>';
    }

    return caption;
  },
});
