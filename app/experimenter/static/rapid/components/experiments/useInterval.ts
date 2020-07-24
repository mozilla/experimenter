// From https://overreacted.io/making-setinterval-declarative-with-react-hooks/
import React from "react";

export default function useInterval(callback: () => void, delay: number): void {
  const savedCallback = React.useRef(callback);
  let id;

  // Remember the latest callback.
  React.useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  // Set up the interval.
  React.useEffect(() => {
    function tick() {
      savedCallback.current();
    }

    if (delay !== null) {
      id = setInterval(tick, delay);
      return () => clearInterval(id);
    }
  }, [id]);
}
