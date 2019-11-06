import React from "react";
import { Button, Container, Row, Col } from "react-bootstrap";
import { boundClass } from "autobind-decorator";

import PrefForm from "experimenter/components/PrefForm";
import GenericForm from "experimenter/components/GenericForm";
import AddonForm from "experimenter/components/AddonForm";

@boundClass
export default class DesignForm extends React.PureComponent {
  constructor(props) {
    super(props);

    this.state = {
      data: {},
      errors: {},
      loaded: false
    };
  }

  async componentDidMount() {
    const response = await this.makeFetchCall("GET");

    const data = await response.json();

    const controlBranchIndex = data.variants.findIndex(
      element => element.is_control
    );
    const controlBranch = data.variants.splice(controlBranchIndex, 1)[0];
    data.variants.unshift(controlBranch);

    this.setState({
      loaded: true,
      data
    });
  }

  addBranch() {
    const { data } = this.state;
    this.setState({
      data: {
        ...data,
        variants: [
          ...data.variants,
          {
            ratio: "",
            name: "",
            description: "",
            value: "",
            is_control: false,
            id: null
          }
        ]
      }
    });
  }

  removeBranch(index) {
    const variants = [...this.state.data.variants];
    variants.splice(index, 1);
    this.setState({
      data: {
        ...this.state.data,
        variants
      }
    });
  }

  handleDataChange(key, value) {
    this.setState({
      data: {
        ...this.state.data,
        [key]: value
      }
    });
  }

  handleValidationErrors(json) {
    this.setState({ errors: json });
  }

  async makeFetchCall(method, body) {
    const url = `/api/v1/experiments/${this.props.slug}/design-${this.props.expType}/`;

    return await fetch(url, {
      method: method,
      body: body,
      headers: {
        "Content-Type": "application/json"
      }
    });
  }

  async handleSubmit(e, url) {
    e.preventDefault();

    // TODO: Refactor this out in an API fetch helper with smarter response handling
    const res = await this.makeFetchCall("PUT", JSON.stringify(this.state.data));

    if (res.status == "200") {
      location.replace(url);
    }

    const json = await res.json();
    this.handleValidationErrors(json);

    const invalid = document.querySelector(".is-invalid");
    if (invalid) {
     invalid.scrollIntoView();
    }
  }

  handleSubmitSave(e) {
    this.handleSubmit(e, `/experiments/${this.props.slug}/`);
  }

  handleSubmitContinue(e) {
    this.handleSubmit(e, `/experiments/${this.props.slug}/edit-objectives/`);
  }

  render() {
    if (!this.state.loaded) {
      return (
        <Container>
          <div className="fa-5x">
            <Row className="justify-content-center">
              <i className="fas fa-spinner fa-spin" />
            </Row>
          </div>
        </Container>
      );
    }

    // Select the appropriate form component to use based on experiment type
    let Form;
    switch (this.state.data.type) {
      case "pref":
        Form = PrefForm;
        break;
      case "addon":
        Form = AddonForm;
      default:
        Form = GenericForm;
    }

    return (
      <div>
        <Container>
          <form onSubmit={this.handleSubmit} id="design-form">
            <Form
              handleDataChange={this.handleDataChange}
              onAddBranch={this.addBranch}
              onRemoveBranch={this.removeBranch}
              data={this.state.data}
              errors={this.state.errors}
              loaded={this.state.loaded}
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
                  variant="primary"
                  type="submit"
                  className="mr-1"
                  onClick={this.handleSubmitSave}
                >
                  <span className="fas fa-save" /> Save Draft
                </Button>

                <Button
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
