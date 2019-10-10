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


export default function AddonForm(props) {
  return (
    <div>
      <Row>
        <Col md={{ span: 4, offset: 3 }}>
          <h4>Firefox Add-On</h4>
        </Col>
      </Row>
      <Row>
        <Col md={3} className="text-right mb-3">
          <FormLabel>
            <strong>Active Experiment Name</strong>
          </FormLabel>
          <br />
          <a href="/">help</a>
        </Col>
        <Col md={9}>
          <FormControl
            type="text"
            name="addon-experiment-id"
            onChange={props.handleInputChange}
            value={props.addon_experiment_id}
            className= {props.errors.addon_experiment_id ? "is-invalid" : "" }
          />
          {props.errors.addon_experiment_id ? <Error error={props.errors.addon_experiment_id}/>  : ""}
        </Col>
      </Row>
      <Row>
        <Col md={3} className="text-right mb-3">
          <FormLabel>
            <strong>Signed Release URL</strong>
          </FormLabel>
          <br />
          <a href="/">help</a>
        </Col>
        <Col md={9}>
          <FormControl
            type="text"
            name="addon-release-url"
            onChange={props.handleInputChange}
            value={props.addon_release_url}
            className= {props.errors.addon_release_url ? "is-invalid" : "" }
          />
          {props.errors.addon_release_url ? <Error error={props.errors.addon_release_url}/>  : ""}
        </Col>
      </Row>
    </div>
  );
}
