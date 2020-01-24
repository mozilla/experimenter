import PropTypes from "prop-types";
import React from "react";
import { Map } from "immutable";
import { Row, Col } from "react-bootstrap";

import DesignInput from "experimenter/components/DesignInput";
import RadioButton from "experimenter/components/RadioButton";
import {
  ADDON_RELEASE_URL_HELP,
  ROLLOUT_PREF_BRANCH_HELP,
  pref_name_HELP,
  PREF_TYPE_BOOL,
  PREF_TYPE_HELP,
  PREF_TYPE_INT,
  PREF_TYPE_JSON_STR,
  PREF_TYPE_STR,
  PREF_VALUE_HELP,
  ROLLOUT_DESCRIPTION_HELP,
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
          id="id_addon_release_url"
          label="Signed Add-On URL"
          name="addon_release_url"
          onChange={value => {
            this.props.handleDataChange("addon_release_url", value);
          }}
          value={this.props.data.get("addon_release_url")}
          error={this.props.errors.get("addon_release_url", "")}
          helpContent={ADDON_RELEASE_URL_HELP}
          labelColumnWidth={2}
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
            helpContent={ROLLOUT_PREF_BRANCH_HELP}
            note="*Note: Pref Rollouts always use the Default Pref Branch"
            labelColumnWidth={2}
          >
            <option>Default Branch</option>
            <option disabled>User Branch</option>
          </DesignInput>

          <DesignInput
            id="id_pref_type"
            label="Pref Type"
            name="pref_type"
            onChange={value => {
              this.props.handleDataChange("pref_type", value);
            }}
            value={this.props.data.get("pref_type")}
            error={this.props.errors.get("pref_type", "")}
            as="select"
            helpContent={PREF_TYPE_HELP}
            labelColumnWidth={2}
          >
            <option>Firefox Pref Type</option>
            <option value={PREF_TYPE_BOOL}>boolean</option>
            <option value={PREF_TYPE_INT}>integer</option>
            <option value={PREF_TYPE_STR}>string</option>
            <option value={PREF_TYPE_JSON_STR}>json string</option>
          </DesignInput>

          <DesignInput
            id="id_pref_name"
            label="Pref Name"
            name="pref_name"
            onChange={value => {
              this.props.handleDataChange("pref_name", value);
            }}
            value={this.props.data.get("pref_name")}
            error={this.props.errors.get("pref_name", "")}
            helpContent={pref_name_HELP}
            labelColumnWidth={2}
          />

          <DesignInput
            id="id_pref_value"
            label="Pref Value"
            name="pref_value"
            onChange={value => {
              this.props.handleDataChange("pref_value", value);
            }}
            value={this.props.data.get("pref_value")}
            error={this.props.errors.get("pref_value", "")}
            helpContent={PREF_VALUE_HELP}
            labelColumnWidth={2}
          />
        </React.Fragment>
      );
    }
  }

  render() {
    return (
      <React.Fragment>
        <Row>
          <Col md={{ span: 10, offset: 2 }}>
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
          id="id_design"
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
          labelColumnWidth={2}
        />

        {this.renderAddonFields()}

        {this.renderPrefFields()}
      </React.Fragment>
    );
  }
}
