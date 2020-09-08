<script>
  import { getContext } from "svelte";

  const xScale = getContext("xScale");
  const graphicWidth = getContext("graphicWidth");
  const top = getContext("topPlot");
  const bottom = getContext("bottomPlot");
  const left = getContext("leftPlot");
  const right = getContext("rightPlot");
  export let x;
  export let line = true;
  export let label = true;
  export let boundary = "graphic"; // vs. plot, or undefined

  function correctLeft(elementLeft, leftBoundary) {
    return Math.abs(Math.max(0, leftBoundary - elementLeft));
  }

  function correctRight(elementRight, rightBoundary) {
    return -Math.max(0, elementRight - rightBoundary);
  }

  $: xp = $xScale(x);

  function correct(element, xr, leftBoundary, rightBoundary) {
    if (element === undefined) return 0;
    const { width: w } = element;
    const l = xr - w / 2;
    const r = xr + w / 2;
    let dl = correctLeft(l, leftBoundary);
    let dr = correctRight(r, rightBoundary);
    if (dl !== 0) return dl;
    return dr;
  }

  let textElement;
  let dx = 0;
  $: if (x && textElement)
    dx = correct(
      textElement.getBBox(),
      xp,
      boundary === "graphic" ? 0 : $left,
      boundary === "graphic" ? $graphicWidth : $right
    );
</script>

<g bind:this={textElement} transform="translate({xp} 0)">
  {#if line}
    <line
      shape-rendering="crispEdges"
      stroke-dasharray="4,2"
      stroke="var(--cool-gray-300)"
      x1="0"
      x2="0"
      y1={$top}
      y2={$bottom} />
  {/if}
  {#if label}
    <text
      font-size="12"
      style="text-transform: uppercase;"
      fill="var(--cool-gray-450)"
      y={$top}
      {dx}
      dy="-.75em"
      text-anchor="middle">
      <slot />
    </text>
  {/if}
</g>
