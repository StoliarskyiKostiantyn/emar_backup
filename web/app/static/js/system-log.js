// Tooltips initialization
const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-toggle="tooltip"]'))
const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
  return new bootstrap.Tooltip(tooltipTriggerEl)
})

const searchInput = document.querySelector("#logs-search-input");
if (searchInput) {
  searchInput.addEventListener("keyup", function (e) {
    if (e.key === "Enter") {
      let oldParams = (new URL(window.location)).searchParams;
      let url = new URL(window.location.href);
      url.searchParams.set("q", searchInput.value);
      // reset page to 1
      url.searchParams.set("page", "1");
      url.searchParams.set("per_page", oldParams.get("per_page") || "25");
      url.searchParams.set("days", oldParams.get("days") || "30");
      url.searchParams.set("type", oldParams.get("type") || "All");
      window.location.href = "".concat(url.href);
    }
  });
}

const clearSearchInput = (e) => {
  searchInput.value = "";
  let oldParams = (new URL(window.location)).searchParams;
  let url = new URL(window.location.href);
  url.searchParams.set("q", "");
  // reset page to 1
  url.searchParams.set("page", "1");
  url.searchParams.set("per_page", oldParams.get("per_page") || "25");
  url.searchParams.set("days", oldParams.get("days") || "30");
  url.searchParams.set("type", oldParams.get("type") || "All");
  window.location.href = "".concat(url.href);
}
