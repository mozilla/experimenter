<script lang="ts">
  import type {
    AnalysisPoint,
    ExperimentAnalysis
  } from "experimenter-types/experiment";

  import { Stack } from "@graph-paper/stack";
  import OneBigGraph from "./components/OneBigGraph.svelte";

  export let experimentData: ExperimentAnalysis;

  let branches = new Set();

  const graphs: Array<{label: string, value: Array<Array<Array<string>>>}> = [
    {label: "Retention", value: [[["binomial", "retained", "daily"], ["binomial", "retained", "weekly"]]]},
    {label: "Search", value: [[["mean", "search_count", "weekly"]]]},
    {label: "Engagement", value: [
      [["mean", "active_hours", "weekly"], ["mean", "uri_count", "weekly"]],
      [["mean", "ad_clicks", "weekly"]]
    ]}
  ];

  const plotTemplate = {
    type: "line",
    x: "window_index",
    y: ["point"],
    xType: "linear",
    group: "branch",
    yAxisFormat: ".0%",
    yMouseoverFormat: ".2%"
  };

  function setBranches() {
    branches.clear();
    for (let datum of experimentData["weekly"]) {
      let { branch } = datum;
      branches.add(branch);
    }
  }

  function getDataByType(info: Array<string>) {
    const [statistic, metric, analysisWindow] = info;

    let fullData: Array<AnalysisPoint>;
    if (analysisWindow === "daily") {
      fullData = experimentData["daily"];
    } else {
      fullData = experimentData["weekly"];
    }
    if (!fullData) {
      return;
    }
    let filteredData = fullData.filter(row => {
      return row["metric"] === metric &&
        row["statistic"] === statistic &&
        !row["comparison_to_branch"] &&
        (row["parameter"] === "0.9" || !("parameter" in row));
    });
    filteredData.sort((a, b) => (a.window_index > b.window_index) ? 1 : -1)
    return filteredData;
  }

  function getPlotByData(info: Array<string>) {
    const [statistic, metric, analysisWindow] = info;

    let title = `${metric.replace(/_/g, " ")} by ${analysisWindow} index`;
    let plot = Object.assign({}, plotTemplate);
    plot["title"] = title;

    if (metric !== "retained") {
      plot["yAxisFormat"] = plot["yMouseoverFormat"] = ".3s"
    }
    return plot;
  }

  $: {
    setBranches();
  }
</script>

<div class="body">
  {#if experimentData}
  <Stack space={2}>
    {#each graphs as graph}
      <div class="subtitle2 indent">Browser {graph.label}</div>
      {#each graph.value as row}
        <div class="row">
          {#if row.length > 1}
          <div class="row_left">
            <OneBigGraph data={getDataByType(row[0])} plot={getPlotByData(row[0])} />
          </div>
          <div class="row_right">
            <OneBigGraph data={getDataByType(row[1])} plot={getPlotByData(row[1])} />
          </div>
          {/if}
        </div>
      {/each}
    {/each}
  </Stack>
  {/if}
</div>
