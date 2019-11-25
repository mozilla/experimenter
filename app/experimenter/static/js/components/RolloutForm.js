import { Map } from "immutable";
import PropTypes from "prop-types";
import React from "react";
import { Row, Col, Form } from "react-bootstrap";

import DesignInput from "experimenter/components/DesignInput";

export default class AddonForm extends React.PureComponent {
  static propTypes = {
    data: PropTypes.instanceOf(Map),
    errors: PropTypes.instanceOf(Map),
    handleDataChange: PropTypes.func,
    handleErrorsChange: PropTypes.func,
  };

  render() {
    return (
      <div>
        <Row className="mb-3">
          <Col md={{ span: 9, offset: 3 }}>
            <h4>Rollout Type</h4>
          </Col>
        </Row>
        <Row className="mb-3">
          <Col md={{ span: 9, offset: 3 }}>
            <Form.Check
              inline
              type="radio"
              name="rollout-type"
              id="rollout-type-pref"
              label="Pref Rollout"
              value="pref"
              onChange={e => {
                this.props.handleDataChange("rollout_type", e.target.value);
              }}
            />
            <Form.Check
              inline
              type="radio"
              name="rollout-type"
              id="rollout-type-addon"
              label="Addon Rollout"
              value="addon"
              onChange={e => {
                this.props.handleDataChange("rollout_type", e.target.value);
              }}
            />
          </Col>
        </Row>

        <DesignInput
          label="Playbook"
          name="rollout_playbook"
          onChange={value => {
            this.props.handleDataChange("rollout_playbook", value);
          }}
          value={this.props.data.get("rollout_playbook")}
          error={this.props.errors.get("rollout_playbook", "")}
          as="select"
          helpContent={
            <div>
              <p>
                <a href="https://mana.mozilla.org/wiki/pages/viewpage.action?pageId=90737068#StagedRollouts/GradualRollouts-Playbooks">
                  Playbook Help
                </a>
              </p>
            </div>
          }
        >
          <option>Select Playbook</option>
          <option value="low_risk">Low Risk</option>
          <option value="high_risk">High Risk</option>
          <option value="marketing">Marketing Launch Schedule</option>
          <option value="custom">Custom</option>
        </DesignInput>

        <DesignInput
          label="Description"
          name="design"
          onChange={value => {
            this.props.handleDataChange("design", value);
          }}
          value={this.props.data.get("design")}
          error={this.props.errors.get("design", "")}
          as="textarea"
          rows="3"
          helpContent={
            <div>
              <p>
                Describe the changes that will be shipped in this rollout and
                how they fill affect users.
              </p>
            </div>
          }
        />

        {this.props.data.get("rollout_type") === "pref" && (
          <div>
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
                    Select the type of the pref entered above. The pref type
                    will be shown in the third column in about:config.
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
              label="Pref Value"
              name="pref_value"
              id="id_pref_value"
              onChange={value => {
                this.props.handleDataChange("pref_value", value);
              }}
              value={this.props.data.get("pref_value")}
              error={this.props.errors.get("pref_value", "")}
              helpContent={
                <div>
                  <p></p>
                  <p></p>
                </div>
              }
            />
            <Row className="mb-3">
              <Col md={{ span: 9, offset: 3 }}>
                <p>
                  *Note: Pref Rollouts always use the{" "}
                  <strong>Default Pref Branch</strong>
                </p>
              </Col>
            </Row>
          </div>
        )}

        {this.props.data.get("rollout_type") === "addon" && (
          <DesignInput
            label="Signed Add-On URL"
            name="addon_release_url"
            onChange={value => {
              this.props.handleDataChange("addon_release_url", value);
            }}
            value={this.props.data.get("addon_release_url")}
            error={this.props.errors.get("addon_release_url", "")}
            helpContent={
              <div>
                <p>
                  Enter the URL where the release build of your add-on can be
                  found. This is often attached to a bugzilla ticket. This MUST
                  BE the release signed add-on (not the test add-on) that you
                  want deployed.&nbsp;
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
          />
        )}
      </div>
    );
  }
}
