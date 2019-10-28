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

export default function Error(props) {
  return (
    <div className="invalid-feedback my-2">
      <span className="fas fa-exclamation"></span> {props.error}
    </div>
  );
}
