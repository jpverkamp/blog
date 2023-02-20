$(() => {
  document.querySelectorAll(".entry-taxonomies").forEach((el) => {
    if (el.innerText.trim().length == 0) {
      el.remove();
    }
  });
});
