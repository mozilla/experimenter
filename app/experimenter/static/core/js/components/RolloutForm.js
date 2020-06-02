import PropTypes from "prop-types";
import React from "react";
import { Map, List, fromJS } from "immutable";
import { Row, Col } from "react-bootstrap";

import DesignInput from "experimenter/components/DesignInput";
import RadioButton from "experimenter/components/RadioButton";
import {
  ADDON_RELEASE_URL_HELP,
  ROLLOUT_DESCRIPTION_HELP,
  TYPE_ADDON,
  TYPE_PREF,
} from "experimenter/components/constants";
import PrefManager from "./PrefManager";

export default class RolloutForm extends React.PureComponent {
  static propTypes = {
    data: PropTypes.instanceOf(Map),
    errors: PropTypes.instanceOf(Map),
    handleDataChange: PropTypes.func,
    handleErrorsChange: PropTypes.func,
    handleReloadAPIState: PropTypes.func,
  };

  renderAddonFields() {
    if (this.props.data.get("rollout_type") === TYPE_ADDON) {
      return (
        <DesignInput
          id="id_addon_release_url"
          label="Signed Add-On URL"
          name="addon_release_url"
          onChange={(value) => {
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
      let blankPreference = fromJS([{ pref_name: "", pref_branch: "" }]);

      return (
        <React.Fragment>
          <PrefManager
            preferences={this.props.data.get("preferences", blankPreference)}
            errors={this.props.errors.get("preferences", new List())}
            onDataChange={(value) => {
              this.props.handleDataChange("preferences", value);
            }}
            onErrorChange={(errors) => {
              this.props.handleErrorsChange("preferences", errors);
            }}
            rolloutType={this.props.data.get("rollout_type")}
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
              choices={[
                { value: TYPE_PREF, label: "Pref Rollout" },
                { value: TYPE_ADDON, label: "Add-On Rollout" },
              ]}
              onChange={(event) =>
                this.props.handleReloadAPIState(
                  "rollout_type",
                  event.target.value,
                )
              }
              value={this.props.data.get("rollout_type")}
            />
          </Col>
        </Row>

        <DesignInput
          id="id_design"
          label="Description"
          name="design"
          onChange={(value) => {
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
