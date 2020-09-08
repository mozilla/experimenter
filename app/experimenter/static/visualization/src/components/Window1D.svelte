<script>
  // eslint-disable-next-line import/no-extraneous-dependencies
  import { getContext } from "svelte";
  import { window1D } from "@graph-paper/core/utils/window-functions";

  export let data;
  export let multi = false;
  export let key;
  export let defaultValue = "latest";

  const x = getContext("xScale");
  const mousePosition = getContext("gp:datagraphic:mousePosition");

  export let value;
  let internalValue;
  $: if (!value) {
    internalValue = $mousePosition.x;
  } else internalValue = value;

  const get = (d, v, k, dom) => {
    const w = window1D({
      value: v,
      data: d,
      key: k,
      lowestValue: dom[0],
      highestValue: dom[1],
    });
    if (w.current) return w.current;
    return 0;
  };
  let output;
  $: if (!multi) {
    output = internalValue
      ? get(data, internalValue, key, $x.domain())
      : data[defaultValue === "latest" ? data.length - 1 : 0];
  } else {
    output = internalValue
      ? data.map(([k, d]) => [k, get(d, internalValue, key, $x.domain())])
      : data.map(([k, d]) => [
          k,
          d[defaultValue === "latest" ? d.length - 1 : 0],
        ]);
  }
</script>

<slot {output} />
