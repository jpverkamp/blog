document.querySelectorAll("a[data-ranked-show]").forEach((el) => {
  el.addEventListener("click", (event) => {
    event.preventDefault();
    const list = el.closest(".ranking");

    list.querySelectorAll("a[data-ranked-show").forEach((a) => {
      if (a === el) {
        a.classList.add("disabled-link");
      } else {
        a.classList.remove("disabled-link");
      }
    });

    if (el.dataset["rankedShow"] === "current") {
      list.querySelectorAll("li[data-future-ranking]").forEach((li) => {
        li.style.display = "none";
      });
    } else {
      list.querySelectorAll("li[data-future-ranking]").forEach((li) => {
        li.style.display = "list-item";
      });
    }
  });
});

document
  .querySelectorAll('a[data-ranked-show="current"]')
  .forEach((el) => el.click());
