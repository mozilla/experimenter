import PropTypes from "prop-types";
import React from "react";

export default function HelpBox(props) {
  let className = "text-muted collapse mt-2";
  if (props.showing) {
    className += " show";
  }

  return <div className={className}>{props.children}</div>;
}

HelpBox.propTypes = {
  children: PropTypes.oneOfType([
    PropTypes.arrayOf(PropTypes.node),
    PropTypes.node,
  ]),
  showing: PropTypes.bool,
};
