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
import HelpBox from "help-box";

export default function PrefValueInput(props) {
  return (
    <Row>
      <Col md={3} className="text-right mb-3">
        <FormLabel>
          <strong>Pref Value</strong>
        </FormLabel>
        <br />
        <a
          href="#"
          id="branch-value"
          data-index={props.index}
          onClick={props.toggleHelp}
        >
          help
        </a>
      </Col>
      <Col md={9}>
        <FormControl
          data-index={props.index}
          type="text"
          id={"variants-" + props.index + "-value"}
          name="value"
          onChange={props.handleVariantInputChange}
          value={props.variants[props.index].value}
          className={props.errors.variants[props.index].value ? "is-invalid" : ""}
        />
        {props.errors.variants[props.index].value ? (
          <Error error={props.errors.variants[props.index].value} />
        ) : (
          ""
        )}
        <HelpBox showing={props.help.variants[props.index].value}>
          <p className="mt-2">
            Choose the value of the pref for the control group. This value must
            be valid JSON in order to be sent to Shield. This should be the
            right type (boolean, string, number), and should be the value that
            represents the control or default state to compare to.
          </p>
          <p>
            <strong>Boolean Example:</strong> false
          </p>
          <p>
            <strong>String Example:</strong> some text
          </p>
          <p>
            <strong>Integer Example:</strong> 13
          </p>
        </HelpBox>
      </Col>
    </Row>
  );
}
