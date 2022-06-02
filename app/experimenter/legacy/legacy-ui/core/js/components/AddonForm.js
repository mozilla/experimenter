import BranchedAddonFields from "experimenter/components/BranchedAddonFields";
import BranchManager from "experimenter/components/BranchManager";
import { ADDON_RELEASE_URL_HELP } from "experimenter/components/constants";
import DesignInput from "experimenter/components/DesignInput";
import GenericBranchFields from "experimenter/components/GenericBranchFields";
import RadioButton from "experimenter/components/RadioButton";
import { List, Map } from "immutable";
import PropTypes from "prop-types";
import React from "react";
import { Col, Row } from "react-bootstrap";

export default class AddonForm extends React.PureComponent {
  static propTypes = {
    data: PropTypes.instanceOf(Map),
    errors: PropTypes.instanceOf(Map),
    handleDataChange: PropTypes.func,
    handleErrorsChange: PropTypes.func,
  };

  renderSingleAddonFields() {
    if (!this.props.data.get("is_branched_addon")) {
      return (
        <div>
          <DesignInput
            label="Signed Add-On URL"
            name="addon_release_url"
            id="signed-addon-url"
            dataTestId="addonUrl"
            onChange={(value) => {
              this.props.handleDataChange("addon_release_url", value);
            }}
            value={this.props.data.get("addon_release_url")}
            error={this.props.errors.get("addon_release_url", "")}
            helpContent={ADDON_RELEASE_URL_HELP}
            labelColumnWidth={2}
          />
        </div>
      );
    }
  }

  render() {
    return (
      <div>
        <Row>
          <Col md={{ span: 10, offset: 2 }}>
            <RadioButton
              elementLabel="How many add-ons does this experiment ship?"
              fieldName="is_branched_addon"
              choices={[
                { value: false, label: "A single add-on for all branches" },
                { value: true, label: "Multiple add-ons" },
              ]}
              onChange={(event) =>
                this.props.handleDataChange(
                  "is_branched_addon",
                  event.target.value === "true",
                )
              }
              value={this.props.data.get("is_branched_addon")}
            />
          </Col>
        </Row>

        {this.renderSingleAddonFields()}

        <hr className="heavy-line my-5" />

        <BranchManager
          branchFieldsComponent={
            this.props.data.get("is_branched_addon")
              ? BranchedAddonFields
              : GenericBranchFields
          }
          branches={this.props.data.get("variants", new List())}
          errors={this.props.errors.get("variants", new List())}
          handleDataChange={this.props.handleDataChange}
          handleErrorsChange={this.props.handleErrorsChange}
        />
      </div>
    );
  }
}
