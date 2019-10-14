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
          <a href="#" id="addon-experiment-id" onClick={props.toggleHelp}>help</a>
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
          <HelpBox showing={props.help.addonExperimentId}>
            <p>
              Enter the <code>activeExperimentName</code> as it appears in the
              add-on. It may appear in <code>manifest.json</code> as
              <code> applications.gecko.id </code>
              <a target="_blank" rel="noreferrer noopener" href="https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-Add-ons">
              See here for more info.</a>
            </p>
          </HelpBox>
        </Col>
      </Row>
      <Row>
        <Col md={3} className="text-right mb-3">
          <FormLabel>
            <strong>Signed Release URL</strong>
          </FormLabel>
          <br />
          <a href="#" id="addon-release-url" onClick={props.toggleHelp}>help</a>
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
          <HelpBox showing={props.help.addonReleaseUrl}>
            <p>
              Enter the URL where the release build of your add-on can be found.
              This is often attached to a bugzilla ticket.
              This MUST BE the release signed add-on (not the test add-on)
              that you want deployed.
              <a target="_blank" rel="noreferrer noopener" href="https://mana.mozilla.org/wiki/display/FIREFOX/Pref-Flip+and+Add-On+Experiments#Pref-FlipandAdd-OnExperiments-Add-ons"> See here for more info.</a>
            </p>
          </HelpBox>
        </Col>
      </Row>
    </div>
  );
}
