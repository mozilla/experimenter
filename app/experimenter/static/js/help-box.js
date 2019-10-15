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
  return (
    <div
      className={
        props.showing
          ? "text-muted collapse show mt-2"
          : "text-muted collapse mt-2"
      }
    >
      {props.children}
    </div>
  );
}
