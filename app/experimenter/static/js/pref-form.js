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


export default function PrefForm(props) {
  return (
    <div>
      <Row>
        <Col md={{ span: 4, offset: 3 }}>
          <h4>Firefox Pref</h4>
        </Col>
      </Row>
      <Row>
        <Col md={3} className="text-right mb-3">
          <FormLabel>
            <strong>Pref Name</strong>
          </FormLabel>
          <br />
          <a href="/">help</a>
        </Col>
        <Col md={9}>
          <FormControl
            type="text"
            name="pref-name"
            value={props.pref_key}
            onChange={props.handleInputChange}
          />
        </Col>
      </Row>
      <Row>
        <Col md={3} className="text-right mb-3">
          <FormLabel>
            <strong>Pref Type</strong>
          </FormLabel>
          <br />
          <a href="/">help</a>
        </Col>
        <Col md={9}>
          <FormControl as="select"
            type="text"
            name="pref-type"
            value={props.pref_type}
            onChange={props.handleInputChange}
          >
            <option>Firefox Pref Type</option>
            <option>boolean</option>
            <option>integer</option>
            <option>string</option>
            <option>json string</option>
          </FormControl>
        </Col>
      </Row>
      <Row>
        <Col md={3} className="text-right mb-3">
          <FormLabel>
            <strong>Pref Branch</strong>
          </FormLabel>
          <br />
          <a href="/">help</a>
        </Col>
        <Col md={9}>
          <FormControl
            type="text"
            name="pref-branch"
            value={props.pref_branch}
            onChange={props.handleInputChange}
          />
        </Col>
      </Row>
    </div>
  );
}
