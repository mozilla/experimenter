import React from "react";

import { SIGNIFICANCE } from "experimenter-rapid/components/visualization/constants/analysis";

const renderBounds = (lower, upper, significance) => {
  const padding = <div className="col p-0"></div>;
  const numbers = (
    <>
      <div
        className={`${significance}-significance col text-left p-0 h6 font-weight-normal`}
      >
        {lower}%
      </div>
      <div
        className={`${significance}-significance col text-right p-0 h6 font-weight-normal`}
      >
        {upper}%
      </div>
    </>
  );

  switch (significance) {
    case SIGNIFICANCE.NEGATIVE:
      return (
        <>
          {numbers}
          {padding}
          {padding}
        </>
      );
    case SIGNIFICANCE.POSITIVE:
      return (
        <>
          {padding}
          {padding}
          {numbers}
        </>
      );
    case SIGNIFICANCE.NEUTRAL:
      return (
        <>
          {padding}
          {numbers}
          {padding}
        </>
      );
  }
};

const renderLine = (significance) => {
  let firstLine, secondLine, thirdLine;
  firstLine = secondLine = thirdLine = "col";

  if (SIGNIFICANCE.NEGATIVE === significance) {
    firstLine = "col-md-1";
    secondLine = "col-md-4";
  }

  if (SIGNIFICANCE.POSITIVE === significance) {
    secondLine = "col-md-4";
    thirdLine = "col-md-1";
  }

  return (
    <>
      <div className={`${firstLine} border-bottom border-dark border-3`} />
      <div
        className={`${secondLine} md-4 ml-md-auto py-2 ${significance} mb-n2`}
      />
      <div className={`${thirdLine} md-1 border-bottom border-dark border-3`} />
    </>
  );
};

const renderTick = (significance) => {
  let position = "py-2";
  if (SIGNIFICANCE.NEUTRAL === significance) {
    position = "py-1 mt-2";
  }

  return <div className={`col border-left border-dark border-3 ${position}`} />;
};

const ConfidenceInterval: React.FC<{
  upper: number;
  lower: number;
  significance: string;
}> = ({ upper, lower, significance }) => {
  const bounds = renderBounds(lower, upper, significance);
  const line = renderLine(significance);
  const tick = renderTick(significance);

  return (
    <div className="container">
      <div className="row w-100 float-right">{bounds}</div>
      <div className="row w-100 float-right">{line}</div>
      <div
        className="row w-50 float-right"
        data-testid={`${significance}-block`}
      >
        {tick}
      </div>
      <div className="row w-100 float-right h6">
        <div className="col d-flex justify-content-center">control</div>
      </div>
    </div>
  );
};

export default ConfidenceInterval;
