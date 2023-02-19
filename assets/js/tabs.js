// Original idea: https://www.w3schools.com/howto/howto_js_tabs.asp

function changeTab(evt, tabset, tabName) {
  // Hide all tabs
  document
    .querySelectorAll(`div.tabcontent[data-tabset="${tabset}"]`)
    .forEach((tab) => {
      tab.style.display = "none";
    });

  // Show the selected tab
  let activeContent = document.querySelector(
    `div.tabcontent#${tabName}[data-tabset="${tabset}"]`
  );
  if (activeContent) {
    activeContent.style.display = "block";
  }

  // If the selected tab has a frame, fix scaling
  let tab = document.querySelector(`div.tabcontent#${tabName}`);
  let frame = tab.querySelector("iframe");
  if (frame) {
    let widthOnPage = tab.clientWidth;
    let widthInFrame = frame.contentWindow.document.body.clientWidth;

    if (widthOnPage < widthInFrame) {
      let scale = widthOnPage / widthInFrame;
      frame.style.transformOrigin = "left top";
      frame.style.transform = `scale(${scale})`;
    }
  }

  // Remove active from all tabs
  document
    .querySelectorAll(`button.tablinks[data-tabset="${tabset}"]`)
    .forEach((tab) => {
      tab.classList.remove("active");
    });

  // Add active to the selected tab
  let activeButton = document.querySelector(
    `button.tablinks#${tabName}[data-tabset="${tabset}"]`
  );
  if (activeButton) {
    activeButton.classList.add("active");
  }
}

$(function () {
  let tabsetset = [];

  document.querySelectorAll("button.tablinks").forEach((el) => {
    let attr = el.attributes["data-tabset"].value;
    if (!tabsetset.includes(attr)) {
      tabsetset.push(attr);
      el.click();
    }
  });
});
