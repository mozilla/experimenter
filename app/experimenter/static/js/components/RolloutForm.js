import PropTypes from "prop-types";
import React from "react";
import { Map } from "immutable";
import { Row, Col } from "react-bootstrap";

import DesignInput from "experimenter/components/DesignInput";
import RadioButton from "experimenter/components/RadioButton";
import {
  ADDON_RELEASE_URL_HELP,
  PREF_KEY_HELP,
  PREF_TYPE_HELP,
  PREF_VALUE_HELP,
} from "experimenter/components/constants";

const TYPE_PREF = "pref";
const TYPE_ADDON = "addon";

export default class RolloutForm extends React.PureComponent {
  static propTypes = {
    data: PropTypes.instanceOf(Map),
    errors: PropTypes.instanceOf(Map),
    handleDataChange: PropTypes.func,
    handleErrorsChange: PropTypes.func,
  };

  renderAddonFields() {
    if (this.props.data.get("rollout_type") === TYPE_ADDON) {
      return (
        <DesignInput
          label="Signed Add-On URL"
          name="addon_release_url"
          onChange={value => {
            this.props.handleDataChange("addon_release_url", value);
          }}
          value={this.props.data.get("addon_release_url")}
          error={this.props.errors.get("addon_release_url", "")}
          helpContent={ADDON_RELEASE_URL_HELP}
        />
      );
    }
  }

  renderPrefFields() {
    if (this.props.data.get("rollout_type") === TYPE_PREF) {
      return (
        <React.Fragment>
          <DesignInput
            label="Pref Name"
            name="pref_key"
            id="id_pref_key"
            onChange={value => {
              this.props.handleDataChange("pref_key", value);
            }}
            value={this.props.data.get("pref_key")}
            error={this.props.errors.get("pref_key", "")}
            helpContent={PREF_KEY_HELP}
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
            helpContent={PREF_TYPE_HELP}
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
            helpContent={PREF_VALUE_HELP}
          />
          <Row className="mb-3">
            <Col md={{ span: 9, offset: 3 }}>
              <p>
                *Note: Pref Rollouts always use the{" "}
                <strong>Default Pref Branch</strong>
              </p>
            </Col>
          </Row>
        </React.Fragment>
      );
    }
  }

  render() {
    return (
      <div>
        <Row>
          <Col md={{ span: 9, offset: 3 }}>
            <RadioButton
              elementLabel="Rollout Type:"
              fieldName="rollout_type"
              radioLabel1="Pref Rollout"
              radioLabel2="Add-On Rollout"
              radioValue1={TYPE_PREF}
              radioValue2={TYPE_ADDON}
              onChange={event =>
                this.props.handleDataChange("rollout_type", event.target.value)
              }
              value={this.props.data.get("rollout_type")}
            />
          </Col>
        </Row>

        <hr className="heavy-line my-5" />

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

        {this.renderAddonFields()}

        {this.renderPrefFields()}
      </div>
    );
  }
}
