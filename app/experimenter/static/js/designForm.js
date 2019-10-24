import React from "react";
import ReactDOM from "react-dom";
import {
  Button,
  Container,
  Row,
  Col,
  FormControl,
  FormLabel
} from "react-bootstrap";
import { boundMethod } from "autobind-decorator";
import PrefForm from "pref-form";
import GenericForm from "generic-form";
import AddonForm from "addon-form";
import Error from "error-form";
import HelpBox from "help-box";
import DesignInput from "design-input";
import Serialize from "form-serialize";

export default class DesignForm extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      loaded: false
    };
  }

  async componentDidMount() {
    const response = await this.makeFetchCall("GET");

    const json = await response.json();

    json.loaded = true;

    return this.setState(json);
  }

  @boundMethod
  addBranch(e) {
    let stateCopy = { ...this.state };

    stateCopy.variants.push({
      ratio: null,
      name: "",
      description: "",
      value: "",
      is_control: false
    });

    this.setState(stateCopy);
  }

  @boundMethod
  removeBranch(e) {
    this.state.variants.splice(e.target.dataset.index, 1);

    this.setState({ variants: this.state.variants });
  }

  @boundMethod
  handleVariantInputChange(e) {
    let stateCopy = { ...this.state.variants };
    let inputName = e.target.name;
    stateCopy[e.target.dataset.index][inputName] = e.target.value;

    this.setState(stateCopy);
  }

  @boundMethod
  handleInputChange(e) {
    let stateCopy = { ...this.state };
    stateCopy[e.target.name] = e.target.value;

    this.setState(stateCopy);
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

  @boundMethod
  async handleSubmit(e) {
    e.preventDefault();

    const form = document.querySelector("#design-form");
    const object = Serialize(form, { hash: true });

    const res = await this.makeFetchCall("PUT", JSON.stringify(object));

    if (res.status == "200") {
      location.replace(`/experiments/${this.props.slug}/`);
    }

    const json = await res.json();
    this.handleValidationErrors(json);
  }

  render() {
    const dataExists = this.state.loaded;
    if (!dataExists) {
      return null;
    } else {
      return (
        <div>
          <Container>
            <form onSubmit={this.handleSubmit} id="design-form">
              {this.state.type == "pref" ? (
                <PrefForm
                  handleInputChange={this.handleInputChange}
                  {...this.state}
                ></PrefForm>
              ) : (
                ""
              )}
              {this.state.type == "addon" ? (
                <AddonForm
                  handleInputChange={this.handleInputChange}
                  {...this.state}
                ></AddonForm>
              ) : (
                ""
              )}
              {this.state.type == "generic" ? (
                <GenericForm
                  handleInputChange={this.handleInputChange}
                  {...this.state}
                ></GenericForm>
              ) : (
                ""
              )}

              <hr className="heavy-line my-5" />
              {this.state.variants.map((branch, index) => (
                <div key={index} id="control-branch-group">
                  <Row className="mb-3">
                    <Col md={{ span: 4, offset: 3 }}>
                      {index == 0 ? (
                        <h4>Control Branch</h4>
                      ) : (
                        <h4>Branch {index}</h4>
                      )}
                    </Col>
                    <Col md={5} className="text-right">
                      {index != 0 ? (
                        <Button
                          variant="danger"
                          data-index={index}
                          onClick={this.removeBranch}
                          id="remove-branch-button"
                        >
                          <span className="fas fa-times"></span> Remove Branch
                        </Button>
                      ) : null}
                    </Col>
                  </Row>
                  <DesignInput
                    label="Branch Size"
                    name={"variants[" + index + "][ratio]"}
                    id={"variants-" + index + "-ratio"}
                    index={index}
                    handleInputChange={this.handleVariantInputChange}
                    value={branch.ratio}
                    error={
                      this.state.errors
                        ? this.state.errors.variants[index].ratio
                        : ""
                    }
                    helpContent={
                      <div>
                        <p>
                          Choose the size of this branch represented as a whole
                          number. The size of all branches together must be
                          equal to 100. It does not have to be exact, so these
                          sizes are simply a recommendation of the relative
                          distribution of the branches.
                        </p>
                        <p>
                          <strong>Example:</strong> 50
                        </p>
                      </div>
                    }
                  ></DesignInput>
                  <DesignInput
                    label="Name"
                    name={"variants[" + index + "][name]"}
                    id={"variants-" + index + "-name"}
                    index={index}
                    handleInputChange={this.handleVariantInputChange}
                    value={branch.name}
                    error={
                      this.state.errors
                        ? this.state.errors.variants[index].name
                        : ""
                    }
                    helpContent={
                      <div>
                        <p>
                          The control group should represent the users receiving
                          the existing, unchanged version of what you're
                          testing. For example, if you're testing making a
                          button larger to see if users click on it more often,
                          the control group would receive the existing button
                          size. You should name your control branch based on the
                          experience or functionality that group of users will
                          be receiving. Don't name it 'Control Group', we
                          already know it's the control group!
                        </p>
                        <p>
                          <strong>Example:</strong> Normal Button Size
                        </p>
                      </div>
                    }
                  ></DesignInput>
                  <DesignInput
                    label="Description"
                    name={"variants[" + index + "][description]"}
                    as="textarea"
                    rows="3"
                    index={index}
                    id={"variants-" + index + "-description"}
                    handleInputChange={this.handleVariantInputChange}
                    value={branch.description}
                    error={
                      this.state.errors
                        ? this.state.errors.variants[index].description
                        : ""
                    }
                    helpContent={
                      <div>
                        <p>
                          Describe the experience or functionality the control
                          group will receive in more detail.
                        </p>
                        <p>
                          <strong>Example:</strong> The control group will
                          receive the existing 80px sign in button located at
                          the top right of the screen.
                        </p>
                      </div>
                    }
                  ></DesignInput>
                  {this.state.type == "pref" ? (
                    <DesignInput
                      label="Pref Value"
                      name={"variants[" + index + "][value]"}
                      id={"variants-" + index + "-value"}
                      index={index}
                      handleInputChange={this.handleVariantInputChange}
                      value={branch.value}
                      error={
                        this.state.errors
                          ? this.state.errors.variants[index].value
                          : ""
                      }
                      margin="mt-4"
                      helpContent={
                        <div>
                          <p className="mt-2">
                            Choose the value of the pref for the control group.
                            This value must be valid JSON in order to be sent to
                            Shield. This should be the right type (boolean,
                            string, number), and should be the value that
                            represents the control or default state to compare
                            to.
                          </p>
                          <p>
                            <strong>Boolean Example:</strong> false
                          </p>
                          <p>
                            <strong>String Example:</strong> some text
                          </p>
                          <p>
                            <strong>Integer Example:</strong> 13
                          </p>
                        </div>
                      }
                    ></DesignInput>
                  ) : (
                    ""
                  )}
                  <FormControl
                    className="d-none"
                    name={"variants[" + index + "][is_control]"}
                    value={index == 0 ? true : false}
                  ></FormControl>
                  <hr className="heavy-line my-5" />
                </div>
              ))}
              <Row>
                <Col className="text-right">
                  <Button
                    id="add-branch-button"
                    variant="success"
                    className="mb-4"
                    onClick={this.addBranch}
                  >
                    <span className="fas fa-plus"/> Add Branch
                  </Button>
                </Col>
              </Row>
              <Row>
                <Col className="text-right">
                  <a
                    className="mr-1 btn btn-default"
                    href={`/experiments/${this.props.slug}/`}
                  >
                    <span className="fas fa-times"></span> Cancel Editing
                  </a>
                  <Button variant="primary" type="submit" className="mr-1">
                    <span className="fas fa-save"/> Save Draft
                  </Button>
                  <Button id="save-continue" variant="primary" type="submit">
                    <span className="fas fa-save"/> Save Draft and Continue
                  </Button>
                </Col>
              </Row>
            </form>
          </Container>
        </div>
      );
    }
  }
}
