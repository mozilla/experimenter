/* global pdfMake */

const setupResultsTableActions = () => {
  const resultTableDropdowns = document.querySelectorAll(
    ".results-table-actions",
  );

  for (const dropdown of resultTableDropdowns) {
    const experimentSlug = dropdown.dataset.experimentSlug;
    const tableAreaID =
      experimentSlug + "-results-" + dropdown.dataset.controllingArea;
    const table = document.getElementById(tableAreaID);
    const exportBtn = dropdown.querySelector(`#export-${tableAreaID}`);

    dropdown
      .querySelector(`#copy-link-${tableAreaID}`)
      ?.addEventListener("click", () => {
        setupCopyResultsLink(table, experimentSlug);
        dropdown.querySelector(".dropdown-menu").classList.remove("show");
      });

    dropdown
      .querySelector(`#copy-table-${tableAreaID}`)
      ?.addEventListener("click", () => {
        setupCopyResultsTable(experimentSlug, dropdown.dataset.controllingArea);
        dropdown.querySelector(".dropdown-menu").classList.remove("show");
      });

    if (exportBtn) {
      const exportOptions =
        exportBtn.parentElement.querySelectorAll(".export-option");
      for (const option of exportOptions) {
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
      }
    }
  }
};

const setupCopyResultsLink = (table, experimentSlug) => {
  const copiedToast = document.getElementById("copy-table-link-toast");

  if (table && copiedToast) {
    const url = `${window.location.origin}/nimbus/${experimentSlug}/results/#${table.id}`;
    navigator.clipboard.writeText(url);
    window.bootstrap.Toast.getOrCreateInstance(copiedToast).show();
  }
};

const setupCopyResultsTable = (experimentSlug, area) => {
  const HTML_MIME_TYPE = "text/html";

  const copiedToast = document.getElementById("copy-table-toast");
  const tableElement = document.getElementById(
    `clipboard-table-${experimentSlug}-${area}`,
  ).outerHTML;
  const spreadSheetRow = new Blob([tableElement], { type: HTML_MIME_TYPE });

  navigator.clipboard
    .write([new ClipboardItem({ [HTML_MIME_TYPE]: spreadSheetRow })])
    .then(() => {
      window.bootstrap.Toast.getOrCreateInstance(copiedToast).show();
    });
};

const setupExportResultsPDF = (experimentSlug, area) => {
  const tableEl = document.getElementById(
    `clipboard-table-${experimentSlug}-${area}`,
  );

  const TRIM_RE = /\s+/g;

  const structuredTable = Array.from(tableEl.rows, (row) =>
    Array.from(row.cells, (cell) =>
      cell.textContent.replace(TRIM_RE, " ").trim(),
    ),
  );

  const colCount = structuredTable[0]?.length ?? 1;
  const widths = new Array(colCount).fill("*");

  // Make the first cell containing the metric area title bold
  const body = structuredTable.map((row, rIdx) =>
    row.map((text, cIdx) => {
      const cell = { text: text ?? "" };
      if (rIdx === 0 && cIdx === 0) {
        cell.bold = true;
      }
      return cell;
    }),
  );

  const docDefinition = {
    content: [
      `Generated on ${new Date().toLocaleString()}`,
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

  document.body.addEventListener("htmx:afterSwap", setupResultsTableActions());
});
