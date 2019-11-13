import { List, Map } from "immutable";
import PropTypes from "prop-types";

import React from "react";
import { Row, Col, Form } from "react-bootstrap";

import BranchManager from "experimenter/components/BranchManager";
import DesignInput from "experimenter/components/DesignInput";
import GenericBranchFields from "experimenter/components/GenericBranchFields";
import BranchedAddonFields from "experimenter/components/BranchedAddonFields";

export default class AddonForm extends React.PureComponent {
  static propTypes = {
    data: PropTypes.instanceOf(Map),
    errors: PropTypes.instanceOf(Map),
    handleDataChange: PropTypes.func,
    handleErrorsChange: PropTypes.func,
    handleBranchedAddonRadio: PropTypes.func,
  };

  renderSingleAddonFields(props) {
    if (!this.props.data.get("is_branched_addon")) {
      return <SingleAddonFields {...props} />;
    }
  }

  render() {
    return (
      <div>
        <Row className="mb-3">
          <Col md={{ span: 4, offset: 3 }}>
            <h4 className="mb-3">Firefox Add-On</h4>
          </Col>
        </Row>

        <Row>
          <Col md={{ span: 9, offset: 3 }}>
            <Form.Group className="mb-3">
              <Form.Label>
                <strong>
                  Does this experiment ship a single addon to all branches or
                  multiple addons?
                </strong>
              </Form.Label>
              <Form.Check
                name="branchedAddonGroup"
                inline
                value="false"
                defaultChecked={!this.props.data.get("is_branched_addon")}
                label="Single Addon"
                type="radio"
                onChange={this.props.handleBranchedAddonRadio}
              />
              <Form.Check
                name="branchedAddonGroup"
                inline
                label="Multiple Addons"
                value="true"
                defaultChecked={this.props.data.get("is_branched_addon")}
                type="radio"
                onChange={this.props.handleBranchedAddonRadio}
              />
            </Form.Group>
          </Col>
        </Row>
        <hr className="heavy-line my-5" />

        {this.renderSingleAddonFields({ ...this.props })}

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

function SingleAddonFields(props) {
  return (
    <React.Fragment>
      <DesignInput
        label="Addon Experiment Name"
        name="addon_experiment_id"
        onChange={value => {
          props.handleDataChange("addon_experiment_id", value);
        }}
        value={props.data.get("addon_experiment_id")}
        error={props.errors.get("addon_experiment_id", "")}
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
          props.handleDataChange("addon_release_url", value);
        }}
        value={props.data.get("addon_release_url")}
        error={props.errors.get("addon_release_url", "")}
        helpContent={
          <div>
            <p>
              Enter the URL where the release build of your add-on can be found.
              This is often attached to a bugzilla ticket. This MUST BE the
              release signed add-on (not the test add-on) that you want
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
    </React.Fragment>
  );
}
