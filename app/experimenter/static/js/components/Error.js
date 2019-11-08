import React from "react";
import PropTypes from "prop-types";

export default function Error(props) {
  return (
    <div className="invalid-feedback my-2">
      <span className="fas fa-exclamation" /> {props.error}
    </div>
  );
}

Error.propTypes = {
  error: PropTypes.array
};
