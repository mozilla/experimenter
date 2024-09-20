document.body.addEventListener("htmx:afterSwap", function () {
  // After reloading the table, we must update the values for status and sort in the sidebar form
  // since it will not have been reloaded in the htmx get call
  const urlParams = new URLSearchParams(window.location.search);
  const sortValue = urlParams.get("sort");
  const statusValue = urlParams.get("status");
  $('#filter-form input[name="status"]').each(
    (i, e) => (e.value = statusValue),
  );
  $('#filter-form input[name="sort"]').each((i, e) => (e.value = sortValue));
});
