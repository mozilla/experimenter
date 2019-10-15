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
import HelpBox from "help-box";
import Error from "error-form";

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
          <span className="text-muted optional-marker">Optional</span>
          <br />
          <a href="#" id="design" onClick={props.toggleHelp}>
            help
          </a>
        </Col>
        <Col md={9}>
          <FormControl
            as="textarea"
            name="design"
            rows={4}
            value={props.design}
            onChange={props.handleInputChange}
          />
          <HelpBox showing={props.help.design}>
            <p>Specify the design of the experiment.</p>
          </HelpBox>
        </Col>
      </Row>
    </div>
  );
}
