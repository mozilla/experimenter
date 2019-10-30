import React from "react";
import { Row, Col } from "react-bootstrap";

import DesignInput from "experimenter/components/DesignInput";
import BranchManager from "experimenter/components/BranchManager";
import PrefBranch from "./PrefBranch";

export default function PrefForm(props) {
  return (
    <div>
      <Row>
        <Col md={{ span: 4, offset: 3 }}>
          <h4>Firefox Pref</h4>
        </Col>
      </Row>
      <DesignInput
        label="Pref Name"
        name="pref_key"
        id="id_pref_key"
        handleInputChange={props.handleInputChange}
        value={props.values.pref_key}
        error={props.errors ? props.errors.pref_key : ""}
        helpContent={
          <div>
            <p>
              Enter the full name of the Firefox pref key that this experiment
              will control. A pref experiment can control exactly one pref, and
              each branch will receive a different value for that pref. You can
              find all Firefox prefs in about:config and any pref that appears
              there can be the target of an experiment.
            </p>
            <p>
              <strong>Example: </strong>
              browser.example.component.enable_large_sign_in_button
            </p>
          </div>
        }
      ></DesignInput>
      <DesignInput
        label="Pref Type"
        name="pref_type"
        id="id_pref_type"
        handleInputChange={props.handleInputChange}
        value={props.values.pref_type}
        error={props.errors ? props.errors.pref_type : ""}
        as="select"
        helpContent={
          <div>
            <p>
              Select the type of the pref entered above. The pref type will be
              shown in the third column in about:config.
            </p>
            <p>
              <strong>Example:</strong> boolean
            </p>
          </div>
        }
      >
        <option>Firefox Pref Type</option>
        <option>boolean</option>
        <option>integer</option>
        <option>string</option>
        <option>json string</option>
      </DesignInput>

      <DesignInput
        label="Pref Branch"
        name="pref_branch"
        id="id_pref_branch"
        handleInputChange={props.handleInputChange}
        value={props.values.pref_branch}
        error={props.errors ? props.errors.pref_branch : ""}
        as="select"
        helpContent={
          <div>
            <p>
              Select the pref branch the experiment will write its pref value
              to. If you're not sure what this means, you should stick to the
              'default' pref branch. Pref branches are a little more complicated
              than can be written here, but you can find
              <a href="https://developer.mozilla.org/en-US/docs/Archive/Add-ons/Code_snippets/Preferences#Default_preferences">
                {" "}
                more information here
              </a>
              .
            </p>
            <p>
              <strong>Example:</strong> default
            </p>
          </div>
        }
      >
        <option>Firefox Pref Branch</option>
        <option>default</option>
        <option>user</option>
      </DesignInput>
      <hr className="heavy-line my-5" />
      <BranchManager {...props} branchComponent={<PrefBranch />} />
    </div>
  );
}
