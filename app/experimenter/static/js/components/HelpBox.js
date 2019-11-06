import React from "react";
import ReactDOM from "react-dom";
import {
  Button,
  Container,
  Row,
  Col,
  FormControl,
  FormLabel
} from "react-bootstrap";

export default function HelpBox(props) {
  let className = "text-muted collapse mt-2";
  if (props.showing) {
    className += " show";
  }

  return <div className={className}>{props.children}</div>;
}
