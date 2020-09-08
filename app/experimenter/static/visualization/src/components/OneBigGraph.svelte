<script lang="ts">
  // eslint-disable-next-line import/no-extraneous-dependencies
  import { format } from "d3-format";
  // eslint-disable-next-line import/no-extraneous-dependencies
  import { fly } from "svelte/transition";
  // eslint-disable-next-line import/no-extraneous-dependencies
  import { timeFormat } from "d3-time-format";
  // eslint-disable-next-line import/no-extraneous-dependencies
  import { schemeCategory10 } from "d3-scale-chromatic";
  import { DataGraphic } from "@graph-paper/datagraphic";
  import { Axis } from "@graph-paper/guides";
  import { Line, Point } from "@graph-paper/elements";

  import Window1D from "./Window1D.svelte";
  import MetricMouseover from "./StackedLabel.svelte";
  import DateMarker from "./DateMarker.svelte";

  import type {
    AnalysisPoint,
    ExperimentAnalysis
  } from "experimenter-types/experiment";

  export let data: Array<AnalysisPoint>;
  export let plot;

  const defaults = {
    type: "line",
    tickColor: "var(--cool-gray-200)",
    labels: [],
    lineSize: [],
    group: undefined,
    xType: "time",
    yType: "linear",
    xTicks: undefined,
    yTicks: undefined,
  };

  const config = { ...defaults, ...plot };

  if (config.xType === "time") {
    data.forEach((di) => {
      const [year, month, day] = di[config.x].split("-");
      di[config.x] = new Date(+year, +month - 1, +day);
    });
  }

  function groupBy(key, d) {
    if (key === undefined) return [[undefined, d]];
    const groups = Array.from(new Set(d.map((di) => di[key])));
    return groups.map((gr) => {
      return [gr, d.filter((di) => di[key] === gr)];
    });
  }

  function toMouseover(pt) {
    // groups.map
    let mouseovers = pt
      .map(([group, d], j) => {
        return config.y.map((y, i) => {
          return {
            x: d[config.x],
            y: d[y],
            color: schemeCategory10[j * config.y.length + i],
            label:
              pt.length > 1 ? group : config.labels[i] || group || "",
          };
        });
      })
      .flat();
    return mouseovers;
  }
  let width;
  let height = 225;
  let right = 240;
  let left = 80;
  let top = 18;

  let ys = data.map((d) => config.y.map((y) => d[y])).flat();
  let yMin = config.yMin !== undefined ? config.yMin : Math.min(...ys);
  let yMax = config.yMax !== undefined ? config.yMax : Math.max(...ys);

  if (config.facet) {
    width = 300;
    height = 200;
    right = 8;
  }

  let mousePosition: {x?: number, body?: string} = {};

  let facetDateFormat = timeFormat("%b %d, %Y");
  let facetValueFormat = format(config.yMouseoverFormat || ",");
</script>

<style>
  .charts {
    flex-wrap: wrap;
    grid-gap: var(--space-3x);
    padding-bottom: var(--space-4x);
  }

  h2 {
    margin: 0px;
    padding: 0px;
    font-size: var(--text-04);
    padding-bottom: var(--space-base);
  }
</style>

<div>
  {#if data.length}
    <div class="label_large indent">{config.title}</div>
    <div class="charts" class:faceted={config.facet !== undefined}>
      {#each groupBy(config.facet, data) as [facet, facetData]}
        <div>
          {#if facet}
            <h2 style="padding-left:{left}px; padding-right: {right}px;">
              {facet}
            </h2>
          {/if}
          <DataGraphic
            xType={config.xType}
            yType={config.yType}
            {width}
            {height}
            bottom={32}
            {left}
            {top}
            xMin={config.xMin}
            xMax={config.xMax}
            bind:mousePosition
            {right}>
            <g slot="background">
              <Axis
                fontSize={config.facet ? '10px' : '13px'}
                side="bottom"
                lineStyle="long"
                ticks={config.xTicks}
                tickColor={config.tickColor}
                tickFormatter={config.xAxisFormat && format(config.xAxisFormat)} />
              <Axis
                side="left"
                fontSize={config.facet ? '10px' : '13px'}
                tickColor={config.tickColor}
                ticks={config.yTicks}
                tickFormatter={config.yAxisFormat && format(config.yAxisFormat)} />
            </g>
            <g slot="body">
              {#each groupBy(config.group, facetData) as [group, d], j (group)}
                {#each config.y as accessor, i (group + accessor)}
                  <Line
                    data={d}
                    x={config.x}
                    y={accessor}
                    color={schemeCategory10[j * config.y.length + i] || 'gray'}
                    size={config.lineSize[i] || 1} />
                {/each}
              {/each}
            </g>
            
          </DataGraphic>

        </div>
      {/each}
    </div>
  {/if}
</div>
