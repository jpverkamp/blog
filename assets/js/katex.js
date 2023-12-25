$(function () {
  $(".latex-block, .latex-inline").each(function (i, el) {
    katex.render(el.innerText, el);
  });

  renderMathInElement(document.body, {
    delimiters: [
      { left: "$$", right: "$$", display: true },
      { left: "$", right: "$", display: false },
    ],
    // • rendering keys, e.g.:
    throwOnError: true,
  });
});
