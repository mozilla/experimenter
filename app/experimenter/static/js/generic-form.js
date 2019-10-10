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

export default function GenericForm(props) {
  return (
    <div>
      <Row>
        <Col md={{ span: 4, offset: 3 }}>
          <h4>Generic</h4>
        </Col>
      </Row>
      <Row>
        <Col md={3} className="text-right mb-3">
          <FormLabel>
            <strong>Design</strong>
          </FormLabel>
          <br />
          <a href="/">help</a>
        </Col>
        <Col md={9}>
          <FormControl
            as="textarea"
            name="design"
            rows={4}
            value={props.design}
            onChange={props.handleInputChange}
          />
        </Col>
      </Row>
    </div>
  );
}
