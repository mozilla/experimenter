import React from "react";
import PropTypes from "prop-types";

export default function HelpBox(props) {
  let className = "text-muted collapse mt-2";
  if (props.showing) {
    className += " show";
  }

  return <div className={className}>{props.children}</div>;
}

HelpBox.propTypes = {
  showing: PropTypes.bool,
  children: PropTypes.object
};
