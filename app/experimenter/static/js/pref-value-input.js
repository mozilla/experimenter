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
import Error from "error-form";


export default function PrefValueInput(props) {
    return (
      <Row>
        <Col md={3} className="text-right mb-3">
          <FormLabel>
            <strong>Pref Value</strong>
          </FormLabel>
          <br />
          <a href="/">help</a>
        </Col>
        <Col md={9}>
          <FormControl
            data-index={props.index}
            type="text"
            name={"variants-" + props.index + "-value"}
            onChange={props.updateValue}
            value={props.variants[props.index].value}
            className= {props.errors.branch_value ? "is-invalid" : "" }
          />
          {props.errors.branch_value ? <Error error={props.errors.branch_value}/>  : ""}
        </Col>
      </Row>
  )
}
