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
import DesignInput from "design-input";

export default function GenericForm(props) {
  return (
    <div>
      <DesignInput
        label="Design"
        name="design"
        handleInputChange={props.handleInputChange}
        value={props.design}
        error={props.errors.design}
        as="textarea"
        rows="10"
        helpContent={
          <div>
            <p>Specify the design of the experiment.</p>
          </div>
        }
      >
      </DesignInput>
    </div>
  );
}
