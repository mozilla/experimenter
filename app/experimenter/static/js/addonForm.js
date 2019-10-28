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
import DesignInput from "design-input";

export default function AddonForm(props) {
  return (
    <div>
      <Row>
        <Col md={{ span: 4, offset: 3 }}>
          <h4 className="mb-3">Firefox Add-On</h4>
        </Col>
      </Row>
      <DesignInput
        label="Addon Experiment Name"
        name="addon_experiment_id"
        handleInputChange={props.handleInputChange}
        value={props.values.addon_experiment_id}
        error={props.errors ? props.errors.addon_experiment_id : ""}
        helpContent={
          <div>
            <p>
              Enter the <code>activeExperimentName</code> as it appears in the
              add-on. It may appear in <code>manifest.json</code> as
              <code> applications.gecko.id </code>
              <a
                target="_blank"
                rel="noreferrer noopener"
                href="https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-Add-ons"
              >
                See here for more info.
              </a>
            </p>
          </div>
        }
      ></DesignInput>
      <DesignInput
        label="Signed Release URL"
        name="addon_release_url"
        handleInputChange={props.handleInputChange}
        value={props.values.addon_release_url}
        error={props.errors ? props.errors.addon_release_url : ""}
        helpContent={
          <div>
            <p>
              Enter the URL where the release build of your add-on can be found.
              This is often attached to a bugzilla ticket. This MUST BE the
              release signed add-on (not the test add-on) that you want
              deployed.
              <a
                target="_blank"
                rel="noreferrer noopener"
                href="https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-Add-ons"
              >
                {" "}
                See here for more info.
              </a>
            </p>
          </div>
        }
      ></DesignInput>
    </div>
  );
}
