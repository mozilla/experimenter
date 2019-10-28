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

import HelpBox from "experimenter/components/HelpBox";
import Error from "experimenter/components/Error";
import DesignInput from "experimenter/components/DesignInput";

export default function GenericForm(props) {
  return (
    <div>
      <DesignInput
        label="Design"
        name="design"
        handleInputChange={props.handleInputChange}
        value={props.values.design}
        error={props.errors ? props.errors.design : ""}
        as="textarea"
        rows="10"
        helpContent={
          <div>
            <p>Specify the design of the experiment.</p>
          </div>
        }
      ></DesignInput>
    </div>
  );
}
