$(function () {
  let toggleButton = document.querySelector(".bingo-toggle");
  if (!toggleButton) return;

  toggleButton.addEventListener("click", () => {
    console.log("toggle");
    console.log(toggleButton.parentNode.querySelector(".bingo"));
    toggleButton.parentNode
      .querySelector(".bingo")
      .classList.toggle("covers-only");
  });

  globalToggleButton = toggleButton;
});
