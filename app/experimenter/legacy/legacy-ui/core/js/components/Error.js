import PropTypes from "prop-types";
import React from "react";

export default function Error(props) {
  return (
    <div className="invalid-feedback my-2">
      <span className="fas fa-exclamation" /> {props.error}
    </div>
  );
}

Error.propTypes = {
  error: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.array,
    PropTypes.object,
  ]),
};
