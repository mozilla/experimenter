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

export default class DesignForm extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      values: {},
      errors: {},
      loaded: false
    };
  }

  async componentDidMount() {
    const response = await this.makeFetchCall("GET");

    const data = await response.json();

    const controlBranchIndex = data.variants.findIndex(element => element.is_control)
    const controlBranch = data.variants.splice(controlBranchIndex, 1)[0]
    data.variants.unshift(controlBranch)

    this.setState({
      loaded:true,
      values:data,
    });
  }

  @boundMethod
  addBranch() {
    const {values} = this.state;
    this.setState({
      values:{
        ...values,
        variants:[
          ...values.variants,
          {},
        ],
      },
    });
  }

  @boundMethod
  removeBranch(index) {
    const variants = [ ...this.state.values.variants ];
    variants.splice(index, 1);
    console.log(variants);
    this.setState({
      values:{
        ...this.state.values,
        variants,
      },
    });
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

  @boundMethod
  handleDataChange(key, value){
    this.setState({
      values:{
        ...this.state.values,
        [key]:value,
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

  @boundMethod
  async handleSubmit(e, url) {
    e.preventDefault();

    const form = document.querySelector("#design-form");
    let object = Serialize(form, { hash: true });

    //remove undefined/deleted variants
    //object.variants = object.variants.filter(item=>item!=undefined);
    object.variants = this.state.values.variants;
    const res = await this.makeFetchCall("PUT", JSON.stringify(object));

    if (res.status == "200") {
        location.replace(url);
    }

    const json = await res.json();
    this.handleValidationErrors(json);
    document.querySelector('.is-invalid').scrollIntoView();
  }

  @boundMethod
  handleSubmitSave(e){
    this.handleSubmit(e,`/experiments/${this.props.slug}/`)

  }

  @boundMethod
  handleSubmitContinue(e){
    this.handleSubmit(e,`/experiments/${this.props.slug}/edit-objectives/`)

  }

  render() {
    if (!this.state.loaded) {
      return (
        <Container>
          <div className="fa-5x">
            <Row className="justify-content-center">
              <i className="fas fa-spinner fa-spin"></i>
            </Row>
          </div>
        </Container>
      );
    } 
    let Form;
    if (this.state.values.type === "pref"){
      Form = PrefForm;
    } else if(this.state.values.type === "addon"){
      Form = AddonForm;
    } else{
      Form = GenericForm;
    }
    return (
      <div>
        <Container>
          <form onSubmit={this.handleSubmit} id="design-form">
            <Form
              handleInputChange={this.handleInputChange}
              handleDataChange={this.handleDataChange}
              onAddBranch={this.addBranch}
              onRemoveBranch={this.removeBranch}
              {...this.state}
            />
            <Row>
              <Col className="text-right">
                <a
                  className="mr-1 btn btn-default"
                  href={`/experiments/${this.props.slug}/`}
                >
                  <span className="fas fa-times"></span> Cancel Editing
                </a>
                <Button variant="primary" type="submit" className="mr-1" onClick={this.handleSubmitSave}>
                  <span className="fas fa-save"/> Save Draft
                </Button>
                <Button id="save-continue" variant="primary" type="submit" onClick={this.handleSubmitContinue}>
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
