import PropTypes from "prop-types";
import React from "react";
import { Button, Container, Row, Col } from "react-bootstrap";
import { boundClass } from "autobind-decorator";
import { fromJS, Map } from "immutable";

import AddonForm from "experimenter/components/AddonForm";
import GenericForm from "experimenter/components/GenericForm";
import PrefForm from "experimenter/components/PrefForm";
import RolloutForm from "experimenter/components/RolloutForm";
import { makeApiRequest } from "experimenter/utils/api";
import {
  TYPE_PREF,
  TYPE_ADDON,
  TYPE_GENERIC,
  TYPE_ROLLOUT,
} from "experimenter/components/constants";

@boundClass
class DesignForm extends React.PureComponent {
  static propTypes = {
    experimentType: PropTypes.string,
    isBranchedAddon: PropTypes.bool,
    isMultiPref: PropTypes.bool,
    slug: PropTypes.string,
  };

  constructor(props) {
    super(props);

    this.state = {
      data: new Map(),
      errors: new Map(),
      loaded: false,
      saving: false,
    };
  }

  isMultiPref() {
    return (
      this.props.experimentType === TYPE_PREF &&
      this.state.data.get("is_multi_pref", this.props.isMultiPref)
    );
  }

  isBranchedAddon() {
    return (
      this.props.experimentType === TYPE_ADDON &&
      this.state.data.get("is_branched_addon", this.props.isBranchedAddon)
    );
  }

  getEndpointUrl() {
    if (this.isBranchedAddon()) {
      return `experiments/${this.props.slug}/design-branched-addon/`;
    }
    if (this.isMultiPref()) {
      return `experiments/${this.props.slug}/design-multi-pref/`;
    }
    return `experiments/${this.props.slug}/design-${this.props.experimentType}/`;
  }

  async componentDidMount() {
    const data = await makeApiRequest(this.getEndpointUrl());

    this.setState({
      loaded: true,
      data: fromJS(data),
    });
  }

  handleDataChange(key, value) {
    this.setState(({ data }) => ({
      data: data.set(key, value),
    }));
  }

  async handleReloadAPIState(key, value) {
    this.setState(
      ({ data }) => ({
        data: data.set(key, value),
        loading: true,
      }),
      async () => {
        const data = await makeApiRequest(this.getEndpointUrl());
        data[key] = value;

        this.setState({
          data: fromJS(data),
          loading: false,
        });
      },
    );
  }

  handleErrorsChange(key, value) {
    this.setState(({ errors }) => ({
      errors: errors.set(key, value),
    }));
  }

  async handleSubmit(event, redirectUrl) {
    event.preventDefault();

    this.setState({ saving: true });
    const requestSave = makeApiRequest(this.getEndpointUrl(), {
      method: "PUT",
      data: this.state.data.toJS(),
    });

    requestSave
      .then(() => {
        location.replace(redirectUrl);
      })
      .catch(err => {
        this.setState({
          errors: fromJS(err.data),
        });

        const invalid = document.querySelector(".is-invalid");
        if (invalid) {
          invalid.scrollIntoView();
        }
      })
      .finally(() => {
        this.setState({
          saving: false,
        });
      });
  }

  handleSubmitSave(event) {
    this.handleSubmit(event, `/experiments/${this.props.slug}/`);
  }

  handleSubmitContinue(event) {
    this.handleSubmit(
      event,
      `/experiments/${this.props.slug}/edit-objectives/`,
    );
  }

  render() {
    if (!this.state.loaded) {
      return (
        <Container>
          <div className="fa-5x" data-testId="spinner">
            <Row className="justify-content-center">
              <i className="fas fa-spinner fa-spin" />
            </Row>
          </div>
        </Container>
      );
    }
    // Select the appropriate form component to use based on experiment type
    let Form;
    switch (this.props.experimentType) {
      case TYPE_PREF:
        Form = PrefForm;
        break;
      case TYPE_ADDON:
        Form = AddonForm;
        break;
      case TYPE_ROLLOUT:
        Form = RolloutForm;
        break;
      case TYPE_GENERIC:
        Form = GenericForm;
        break;
    }

    return (
      <div>
        <Container>
          <form onSubmit={this.handleSubmit} id="design-form">
            <Form
              handleDataChange={this.handleDataChange}
              handleErrorsChange={this.handleErrorsChange}
              data={this.state.data}
              errors={this.state.errors}
              loaded={this.state.loaded}
              handleReloadAPIState={this.handleReloadAPIState}
            />
            <Row>
              <Col className="text-right">
                <a
                  className="mr-1 btn btn-default"
                  href={`/experiments/${this.props.slug}/`}
                >
                  <span className="fas fa-times" /> Cancel Editing
                </a>

                <Button
                  disabled={this.state.saving}
                  variant="primary"
                  type="submit"
                  className="mr-1"
                  onClick={this.handleSubmitSave}
                >
                  <span className="fas fa-save" /> Save Draft
                </Button>

                <Button
                  disabled={this.state.saving}
                  id="save-continue"
                  variant="primary"
                  type="submit"
                  onClick={this.handleSubmitContinue}
                >
                  <span className="fas fa-save" /> Save Draft and Continue
                </Button>
              </Col>
            </Row>
          </form>
        </Container>
      </div>
    );
  }
}

export default DesignForm;
