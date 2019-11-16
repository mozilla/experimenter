import { Map } from "immutable";
import PropTypes from "prop-types";
import React from "react";
import { Row, Col } from "react-bootstrap";

import BranchManager from "experimenter/components/BranchManager";
import DesignInput from "experimenter/components/DesignInput";
import PrefBranchFields from "experimenter/components/PrefBranchFields";

export default class PrefForm extends React.PureComponent {
  static propTypes = {
    data: PropTypes.instanceOf(Map),
    errors: PropTypes.instanceOf(Map),
    handleDataChange: PropTypes.func,
    onAddBranch: PropTypes.func,
    onRemoveBranch: PropTypes.func,
  };

  render() {
    return (
      <div>
        <Row className="mb-3">
          <Col md={{ span: 4, offset: 3 }}>
            <h4>Firefox Pref</h4>
          </Col>
        </Row>

        <DesignInput
          label="Pref Name"
          name="pref_key"
          id="id_pref_key"
          onChange={value => {
            this.props.handleDataChange("pref_key", value);
          }}
          value={this.props.data.get("pref_key")}
          error={this.props.errors.get("pref_key", "")}
          helpContent={
            <div>
              <p>
                Enter the full name of the Firefox pref key that this experiment
                will control. A pref experiment can control exactly one pref,
                and each branch will receive a different value for that pref.
                You can find all Firefox prefs in about:config and any pref that
                appears there can be the target of an experiment.
              </p>
              <p>
                <strong>Example: </strong>
                browser.example.component.enable_large_sign_in_button
              </p>
            </div>
          }
        />

        <DesignInput
          label="Pref Type"
          name="pref_type"
          id="id_pref_type"
          onChange={value => {
            this.props.handleDataChange("pref_type", value);
          }}
          value={this.props.data.get("pref_type")}
          error={this.props.errors.get("pref_type", "")}
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
          onChange={value => {
            this.props.handleDataChange("pref_branch", value);
          }}
          value={this.props.data.get("pref_branch")}
          error={this.props.errors.get("pref_branch", "")}
          as="select"
          helpContent={
            <div>
              <p>
                Select the pref branch the experiment will write its pref value
                to. If you're not sure what this means, you should stick to the
                'default' pref branch. Pref branches are a little more
                complicated than can be written here, but you can find&nbsp;
                <a href="https://developer.mozilla.org/en-US/docs/Archive/Add-ons/Code_snippets/Preferences#Default_preferences">
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

        <BranchManager
          branches={this.props.data.get("variants")}
          onAddBranch={this.props.onAddBranch}
          onRemoveBranch={this.props.onRemoveBranch}
          onChange={value => {
            this.props.handleDataChange("variants", value);
          }}
          branchFieldsComponent={PrefBranchFields}
          errors={this.props.errors}
        />
      </div>
    );
  }
}
