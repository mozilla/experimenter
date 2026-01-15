/* global pdfMake */

const setupResultsTableActions = () => {
  const resultTableDropdowns = document.querySelectorAll(
    ".results-table-actions",
  );

  resultTableDropdowns.forEach((dropdown) => {
    const experimentSlug = dropdown.dataset.experimentSlug;
    const tableAreaID =
      experimentSlug + "-results-" + dropdown.dataset.controllingArea;
    const table = document.getElementById(tableAreaID);
    const copyLinkBtn = dropdown.querySelector(`#copy-link-${tableAreaID}`);
    const copyTableBtn = dropdown.querySelector(`#copy-table-${tableAreaID}`);
    const exportBtn = dropdown.querySelector(`#export-${tableAreaID}`);

    if (copyLinkBtn) {
      copyLinkBtn.addEventListener("click", () => {
        setupCopyResultsLink(table, experimentSlug);
        dropdown.querySelector(".dropdown-menu").classList.remove("show");
      });
    }

    if (copyTableBtn) {
      copyTableBtn.addEventListener("click", () => {
        setupCopyResultsTable(experimentSlug, dropdown.dataset.controllingArea);
        dropdown.querySelector(".dropdown-menu").classList.remove("show");
      });
    }

    if (exportBtn) {
      const exportOptions =
        exportBtn.parentElement.querySelectorAll(".export-option");
      exportOptions.forEach((option) => {
        const format = option.dataset.exportFormat;

        switch (format) {
          case "pdf":
            option.addEventListener("click", () => {
              setupExportResultsPDF(
                experimentSlug,
                dropdown.dataset.controllingArea,
              );
            });
            break;
          default:
            console.warn("Unknown export format: ", format);
        }
      });
    }
  });
};

const setupCopyResultsLink = (table, experimentSlug) => {
  var copiedToast = document.getElementById("copy-table-link-toast");

  if (table && copiedToast) {
    const url =
      window.location.origin +
      `/nimbus/${experimentSlug}/results-new/#${table.id}`;
    navigator.clipboard.writeText(url);
    var toast = window.bootstrap.Toast.getOrCreateInstance(copiedToast);
    toast.show();
  }
};

const setupCopyResultsTable = (experimentSlug, area) => {
  const type = "text/html";

  var copiedToast = document.getElementById("copy-table-toast");
  var tableElement = document.getElementById(
    `clipboard-table-${experimentSlug}-${area}`,
  ).outerHTML;
  const spreadSheetRow = new Blob([tableElement], { type });

  navigator.clipboard
    .write([new ClipboardItem({ [type]: spreadSheetRow })])
    .then(() => {
      var toast = window.bootstrap.Toast.getOrCreateInstance(copiedToast);
      toast.show();
    });
};

const setupExportResultsPDF = (experimentSlug, area) => {
  const tableEl = document.getElementById(
    `clipboard-table-${experimentSlug}-${area}`,
  );

  const structuredTable = Array.from(tableEl.rows).map((row) =>
    Array.from(row.cells).map((cell) =>
      cell.textContent.replace(/\s+/g, " ").trim(),
    ),
  );

  const colCount = (structuredTable[0] && structuredTable[0].length) || 1;
  const widths = new Array(colCount).fill("*");

  // Make the first cell containing the metric area title bold
  const body = structuredTable.map((row, rIdx) =>
    row.map((text, cIdx) => {
      const cell = { text: text || "" };
      if (rIdx === 0 && cIdx === 0) cell.bold = true;
      return cell;
    }),
  );

  const docDefinition = {
    content: [
      {
        layout: "lightHorizontalLines",
        table: {
          headerRows: 1,
          widths: widths,
          body: body,
        },
      },
    ],
    defaultStyle: { fontSize: 10 },
  };

  pdfMake
    .createPdf(docDefinition)
    .download(`${experimentSlug}-${area}-results.pdf`);
};

document.addEventListener("DOMContentLoaded", function () {
  setupResultsTableActions();

  document.body.addEventListener("htmx:afterSwap", function () {
    setupResultsTableActions();
  });
});
