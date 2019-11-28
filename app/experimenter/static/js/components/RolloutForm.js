import PropTypes from "prop-types";
import React from "react";
import { Map } from "immutable";
import { Row, Col } from "react-bootstrap";

import DesignInput from "experimenter/components/DesignInput";
import RadioButton from "experimenter/components/RadioButton";
import {
  ADDON_RELEASE_URL_HELP,
  PREF_BRANCH_HELP,
  PREF_KEY_HELP,
  PREF_TYPE_BOOL,
  PREF_TYPE_HELP,
  PREF_TYPE_INT,
  PREF_TYPE_JSON_STR,
  PREF_TYPE_STR,
  PREF_VALUE_HELP,
  ROLLOUT_DESCRIPTION_HELP,
  ROLLOUT_PLAYBOOK_CUSTOM,
  ROLLOUT_PLAYBOOK_HELP,
  ROLLOUT_PLAYBOOK_HIGH_RISK,
  ROLLOUT_PLAYBOOK_LOW_RISK,
  ROLLOUT_PLAYBOOK_MARKETING,
  TYPE_ADDON,
  TYPE_PREF,
} from "experimenter/components/constants";

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
            label="Pref Branch"
            as="select"
            helpContent={PREF_BRANCH_HELP}
            note="*Note: Pref Rollouts always use the Default Pref Branch"
          >
            <option>Default Branch</option>
            <option disabled>User Branch</option>
          </DesignInput>

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
            <option value={PREF_TYPE_BOOL}>boolean</option>
            <option value={PREF_TYPE_INT}>integer</option>
            <option value={PREF_TYPE_STR}>string</option>
            <option value={PREF_TYPE_JSON_STR}>json string</option>
          </DesignInput>

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
        </React.Fragment>
      );
    }
  }

  render() {
    return (
      <React.Fragment>
        <Row>
          <Col md={{ span: 9, offset: 3 }}>
            <RadioButton
              elementLabel="What type of rollout is this?"
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

        <DesignInput
          label="Playbook"
          name="rollout_playbook"
          onChange={value => {
            this.props.handleDataChange("rollout_playbook", value);
          }}
          value={this.props.data.get("rollout_playbook")}
          error={this.props.errors.get("rollout_playbook", "")}
          as="select"
          helpContent={ROLLOUT_PLAYBOOK_HELP}
        >
          <option>Select Playbook</option>
          <option value={ROLLOUT_PLAYBOOK_LOW_RISK}>Low Risk</option>
          <option value={ROLLOUT_PLAYBOOK_HIGH_RISK}>High Risk</option>
          <option value={ROLLOUT_PLAYBOOK_MARKETING}>
            Marketing Launch Schedule
          </option>
          <option value={ROLLOUT_PLAYBOOK_CUSTOM}>Custom</option>
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
          helpContent={ROLLOUT_DESCRIPTION_HELP}
        />

        {this.renderAddonFields()}

        {this.renderPrefFields()}
      </React.Fragment>
    );
  }
}
