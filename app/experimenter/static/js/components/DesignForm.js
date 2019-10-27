import React from "react";
import {
  Button,
  Container,
  Row,
  Col
} from "react-bootstrap";
import { boundMethod } from "autobind-decorator";
import Serialize from "form-serialize";

import PrefForm from "experimenter/components/PrefForm";
import GenericForm from "experimenter/components/GenericForm";
import AddonForm from "experimenter/components/AddonForm";
import BranchManager from "experimenter/components/BranchManager";

export default class DesignForm extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      values: {},
      errors: {},
      continue: false,
      loaded: false
    };
  }

  async componentDidMount() {
    const response = await this.makeFetchCall("GET");

    const data = await response.json();

    const controlBranchIndex = data.variants.findIndex(element => element.is_control)
    const controlBranch = data.variants.splice(controlBranchIndex, 1)[0]
    data.variants.unshift(controlBranch)

    data.loaded = true;

    return this.setState({values: data});
  }

  @boundMethod
  addBranch(e) {
    let stateCopy = { ...this.state.values };

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
    this.state.values.variants.splice(e.target.dataset.index, 1);

    this.setState({ variants: this.state.values.variants });
  }

  @boundMethod
  handleVariantInputChange(e) {
    let stateCopy = { ...this.state.values.variants };
    let inputName = e.target.name;
    stateCopy[e.target.dataset.index][inputName] = e.target.value;

    this.setState(stateCopy);
  }

  @boundMethod
  handleInputChange(e) {
    let stateCopy = { ...this.state.values };
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
    let object = Serialize(form, { hash: true });
  
    //remove undefined/deleted variants
    object.variants = object.variants.filter(item=>item!=undefined);

    const res = await this.makeFetchCall("PUT", JSON.stringify(object));

    if (res.status == "200") {
      if (this.state.continue){
        location.replace(`/experiments/${this.props.slug}/edit-objectives/`);
      }
      else{
        location.replace(`/experiments/${this.props.slug}/`);
      }
      
    }

    const json = await res.json();
    this.handleValidationErrors(json);
  }

  @boundMethod
  setContinue(e){
    this.setState({continue:true})
  }

  render() {
    const dataExists = this.state.values.loaded;
    if (!dataExists) {
      return (
        <Container>
          <div className="fa-5x">
            <Row className="justify-content-center">
              <i className="fas fa-spinner fa-spin"></i>
            </Row>
          </div>
        </Container>
      );
    } else {
      return (
        <div>
          <Container>
            <form onSubmit={this.handleSubmit} id="design-form">
              {this.state.values.type == "pref" ? (
                <PrefForm
                  handleInputChange={this.handleInputChange}
                  {...this.state}
                ></PrefForm>
              ) : (
                ""
              )}
              {this.state.values.type == "addon" ? (
                <AddonForm
                  handleInputChange={this.handleInputChange}
                  {...this.state}
                ></AddonForm>
              ) : (
                ""
              )}
              {this.state.values.type == "generic" ? (
                <GenericForm
                  handleInputChange={this.handleInputChange}
                  {...this.state}
                ></GenericForm>
              ) : (
                ""
              )}             
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
                  <Button id="save-continue" variant="primary" type="submit" onClick={this.setContinue}>
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
