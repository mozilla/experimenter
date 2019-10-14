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
          <a href="#" id="pref-key" onClick={props.toggleHelp}>help</a>
        </Col>
        <Col md={9}>
          <FormControl
            type="text"
            name="pref-name"
            value={props.pref_key}
            onChange={props.handleInputChange}
          />
          {props.errors.pref_key ? <Error error={props.errors.pref_key}/>  : ""}
          <HelpBox showing={props.help.prefKey}>
            <p>
              Enter the full name of the Firefox pref key that this
              experiment will control. A pref experiment can control
              exactly one pref, and each branch will receive a different
              value for that pref. You can find all Firefox prefs in
              about:config and any pref that appears there can be the
              target of an experiment.
            </p>
            <p>
              <strong>Example: </strong>
              browser.example.component.enable_large_sign_in_button
            </p>
          </HelpBox>
        </Col>
      </Row>
      <Row>
        <Col md={3} className="text-right mb-3">
          <FormLabel>
            <strong>Pref Type</strong>
          </FormLabel>
          <br />
          <a href="#" id="pref-type" onClick={props.toggleHelp}>help</a>
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
          {props.errors.pref_type ? <Error error={props.errors.pref_type}/>  : ""}
          <HelpBox showing={props.help.prefType}>
            <p>
              Select the type of the pref entered above.
              The pref type will be shown in the third
              column in about:config.
            </p>
            <p>
              <strong>Example:</strong> boolean
            </p>
          </HelpBox>
        </Col>
      </Row>
      <Row>
        <Col md={3} className="text-right mb-3">
          <FormLabel>
            <strong>Pref Branch</strong>
          </FormLabel>
          <br />
          <a href="#" id="pref-branch" onClick={props.toggleHelp}>help</a>
        </Col>
        <Col md={9}>
          <FormControl
            type="text"
            name="pref-branch"
            value={props.pref_branch}
            onChange={props.handleInputChange}
          />
          {props.errors.pref_branch ? <Error error={props.errors.pref_branch}/>  : ""}
          <HelpBox showing={props.help.prefBranch}>
            <p>
              Select the pref branch the experiment will write its
              pref value to. If you're not sure what this means,
              you should stick to the 'default' pref branch. Pref
              branches are a little more complicated than can be
              written here, but you can find
              <a href="https://developer.mozilla.org/en-US/docs/Archive/Add-ons/Code_snippets/Preferences#Default_preferences"> more information here</a>.
            </p>
            <p>
              <strong>Example:</strong> default
            </p>
          </HelpBox>
        </Col>
      </Row>
    </div>
  );
}
