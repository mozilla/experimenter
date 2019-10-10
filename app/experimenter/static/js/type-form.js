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
import PrefForm from "pref-form";
import AddonForm from "addon-form";
import GenericForm from "generic-form";

export default function TypeForm(props) {
  const type = props.type;

  if (type == "pref") {
    return <PrefForm {...props}/>;
  } else if (type == "addon") {
    return <AddonForm {...props}/>;
  } else {
    return <GenericForm {...props}/>;
  }
}
