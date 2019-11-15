import { Map } from "immutable";
import PropTypes from "prop-types";
import React from "react";
import { Row, Col } from "react-bootstrap";

import BranchManager from "experimenter/components/BranchManager";
import DesignInput from "experimenter/components/DesignInput";
import GenericBranchFields from "experimenter/components/GenericBranchFields";

export default class AddonForm extends React.PureComponent {
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
            <h4 className="mb-3">Firefox Add-On</h4>
          </Col>
        </Row>

        <DesignInput
          label="Addon Experiment Name"
          name="addon_experiment_id"
          onChange={value => {
            this.props.handleDataChange("addon_experiment_id", value);
          }}
          value={this.props.data.get("addon_experiment_id")}
          error={this.props.errors.get("addon_experiment_id", "")}
          helpContent={
            <div>
              <p>
                Enter the <code>activeExperimentName</code> as it appears in the
                add-on. It may appear in <code>manifest.json</code> as
                <code> applications.gecko.id </code>
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

        <DesignInput
          label="Signed Release URL"
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
                found. This is often attached to a bugzilla ticket. This MUST BE
                the release signed add-on (not the test add-on) that you want
                deployed.&nbsp;
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

        <hr className="heavy-line my-5" />

        <BranchManager
          branches={this.props.data.get("variants")}
          onAddBranch={this.props.onAddBranch}
          onRemoveBranch={this.props.onRemoveBranch}
          onChange={value => {
            this.props.handleDataChange("variants", value);
          }}
          branchFieldsComponent={GenericBranchFields}
          errors={this.props.errors}
        />
      </div>
    );
  }
}
