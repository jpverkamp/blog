$(function () {
  $(".latex-block, .latex-inline").each(function (i, el) {
    katex.render(el.innerText, el);
  });
});
